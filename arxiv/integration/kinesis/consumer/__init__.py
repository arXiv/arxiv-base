"""
Provides base classes and tools for building agents (Kinesis consumers).

We use Kinesis streams to broker notifications that concern multiple services
in the arXiv system. For example, at publication time, the publication process
generates notifications about new arXiv papers so that services like search
can update themselves.

This module provides a base class for building agents with Kinesis streams,
:class:`.BaseConsumer`. The objective is to provide all of the
stream-management (e.g. checkpointing) and error-handling boilerplate needed
for any Kinesis consumer, so that we can focus on building the idiosyncratic
functional bits in arXiv services.

Using :class:`.BaseConsumer`
============================

You (the developer) should be able to create a minimal agent by:

1. Defining a class that inherits from :class:`.BaseConsumer`
2. Defining an instace method on that class with the signature:
   ``def process_record(self, record: dict) -> None:`` that implements
   application-specific processing for each notification.
3. Calling :func:`.process_stream` with your consumer class and an application
   config (e.g. from Flask).

Your config should include the following:

``KINESIS_STREAM`` : str
    Name of the stream to consume.
``KINESIS_SHARD_ID`` : str
    E.g. ``"shardId-000000000000"``.
``AWS_ACCESS_KEY_ID`` : str
    Access key ID with read access to Kinesis streams.
``AWS_SECRET_ACCESS_KEY`` : str
    Secret access key with read access to Kinesis streams.
``AWS_REGION`` : str
    E.g. ``us-east-1``.
``KINESIS_ENDPOINT`` : str
    This should be ``None`` in production, but can be set to something else
    for integration testing (e.g. with localstack).
``KINESIS_VERIFY`` : str
    This should be ``"true"`` in production, but can be disabled when doing
    integration testing (since localstack certs won't verify).
``KINESIS_START_TYPE``: str
    How to get the first shard iterator (if a starting position is not
    available via the checkpointer). Currently supports ``TRIM_HORIZON``
    and ``AT_TIMESTAMP``.
``KINESIS_START_AT`` : str
    If using ``AT_TIMESTAMP``, the point of time from which to start in the
    stream. Should have the format ``'%Y-%m-%dT%H:%M:%S'``.

If you're using the provided :class:`.DiskCheckpointManager` provided here
(used by default in :func:`.process_stream`), you should also set:

``KINESIS_CHECKPOINT_VOLUME`` : str
    Full path to a directory where the consumer should store its position.
    Must be readable/writeable.


Testing and development
=======================

The easiest way to write tests for Kinesis consumers is to mock the
[``boto3.client`` factory](http://boto3.readthedocs.io/en/latest/reference/services/kinesis.html).
Unit tests for this module can be found in :mod:`arxiv.base.agent.tests`,
most of which mock boto3 in this way.

For integration tests, or developing against a "live" Kinesis stream,
[Localstack](https://github.com/localstack/localstack) provides a Kinesis
for testing/development purposes (port 4568). You can use the config
parameters above to point to a local instance of localstack (e.g. run with
Docker).

"""

import time
import json
from pytz import UTC
from datetime import datetime, timedelta
import os
from typing import Any, Optional, Tuple, Generator, Callable, Dict, Union, Any
from contextlib import contextmanager
import signal
import warnings

import boto3
from botocore.exceptions import WaiterError, NoCredentialsError, \
    PartialCredentialsError, BotoCoreError, ClientError

from retry.api import retry_call

import logging
from .exceptions import CheckpointError, StreamNotAvailable, StopProcessing, \
    KinesisRequestFailed, ConfigurationError, RestartProcessing

logger = logging.getLogger(__name__)
# logger.propagate = False
logger.setLevel(10)

NOW = datetime.now(tz=UTC).strftime('%Y-%m-%dT%H:%M:%S')


class DiskCheckpointManager(object):
    """
    Provides on-disk loading and updating of consumer checkpoints.

    You can substitute any other mechanism that you prefer for checkpointing
    when you instantiate your consumer, so long as the passed object:

    1. Has an instance method ``checkpoint(self, position: str) -> None:`` that
       stores ``position``, and
    2. Exposes a property ``.position`` that is the last value passed to
       ``checkpoint``.

    """

    def __init__(self, base_path: str, stream_name: str, shard_id: str) \
            -> None:
        """Load or create a new file for checkpointing."""
        if not os.path.exists(base_path):
            raise ValueError(f'Path does not exist: {base_path}')
        self.file_path = os.path.join(base_path,
                                      f'{stream_name}__{shard_id}.json')
        if not os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'w') as f:
                    f.write('')
            except Exception as ex:   # The containing path doesn't exist.
                raise ValueError(f'Could not use {self.file_path}') from ex

        with open(self.file_path) as f:
            position = f.read()
        self.position = position if position else None

    def checkpoint(self, position: str) -> None:
        """Checkpoint at ``position``."""
        try:
            with open(self.file_path, 'w') as f:
                f.write(position)
            self.position = position
        except Exception as ex:
            raise CheckpointError('Could not checkpoint') from ex


class BaseConsumer(object):
    """
    Kinesis stream consumer.

    Consumes a single shard from a single stream, and checkpoints on disk
    (to reduce external dependencies).
    """

    def __init__(self, stream_name: str = '', shard_id: str = '',
                 access_key: Optional[str] = None,
                 secret_key: Optional[str] = None,
                 region: str = '',
                 checkpointer: Optional[DiskCheckpointManager] = None,
                 back_off: int = 5, batch_size: int = 50,
                 endpoint: Optional[str] = None, verify: bool = True,
                 duration: Optional[int] = None,
                 start_type: str = 'AT_TIMESTAMP',
                 start_at: str = NOW, tries: int = 5, delay: int = 5,
                 max_delay: Optional[int] = None, backoff: int = 1,
                 jitter: Union[int, Tuple[int, int]] = 0, **extra: Any) -> None:
        """Initialize a new stream consumer."""
        logger.info(f'New consumer for {stream_name} ({shard_id})')
        self.stream_name = stream_name
        self.shard_id = shard_id
        self.checkpointer = checkpointer
        if self.checkpointer:
            self.position = self.checkpointer.position
        else:
            self.position = None
        self.duration = duration
        self.start_time: Optional[float] = None
        self.back_off = back_off
        self.batch_size = batch_size
        self.sleep_time = 1
        self.start_at = start_at
        self.start_type = start_type
        self._access_key = access_key
        self._secret_key = secret_key
        logger.info(f'Got start_type={start_type} and start_at={start_at}')

        # Retry parameters.
        self.retry_params = {
            'tries': tries,
            'delay': delay,
            'max_delay': max_delay,
            'backoff': backoff,
            'jitter': jitter  #  extra seconds added to delay between retry attempts.
        }

        if not self.stream_name or not self.shard_id:
            logger.info('No stream set; no attempt to connect to Kinesis')
            raise RuntimeError('Stream and shard must be specified')

        self.endpoint = endpoint
        self.verify = verify
        self.region = region

        # Intercept SIGINT and SIGTERM so that we can checkpoint before exit.
        self.exit = False
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        logger.info('Ready to start')

    def get_or_create_stream(self) -> None:
        """Wait for the stream, and create it if it doesn't exist."""
        logger.info(f'Waiting for {self.stream_name} to be available')
        try:
            self.wait_for_stream(tries=1)
        except (KinesisRequestFailed, StreamNotAvailable):
            logger.info('Could not connect to stream; attempting to create')
            self.client.create_stream(StreamName=self.stream_name,
                                      ShardCount=1)
            logger.info(f'Created; waiting for {self.stream_name} again')
            self.wait_for_stream(**self.retry_params)   # type: ignore

    def stop(self, signal: int, frame: Any) -> None:
        """Set exit flag for a graceful stop."""
        logger.error(f'Received signal {signal}')
        self._checkpoint()
        logger.error('Done')
        raise StopProcessing(f'Received signal {signal}')

    def new_client(self) -> boto3.client:
        """Generate a new Kinesis client."""
        params: Dict[str, Any] = {'region_name': self.region,
                                  'aws_access_key_id': self._access_key,
                                  'aws_secret_access_key': self._secret_key}
        client_params: Dict[str, Any] = {}
        if self.endpoint:
            client_params['endpoint_url'] = self.endpoint
        if self.verify is False:
            client_params['verify'] = False

        logger.debug('New session with parameters: %s', params)
        # We don't want to let boto3 manage the Session for us.
        self._session = boto3.Session(**params)

        return self._session.client('kinesis', **client_params)

    def wait_for_stream(self, tries: int = 5, delay: int = 5,
                        max_delay: Optional[int] = None, backoff: int = 2,
                        jitter: Union[int, Tuple[int, int]] = 0) -> None:
        """
        Wait for the stream to become available.

        If the stream becomes available, returns ``None``. Otherwise, raises
        a :class:`.StreamNotAvailable` exception.

        Raises
        ------
        :class:`.StreamNotAvailable`
            Raised when the stream could not be reached.

        """
        waiter = self.client.get_waiter('stream_exists')
        try:
            logger.error(f'Waiting for stream {self.stream_name}')
            fkwargs = {
                'StreamName': self.stream_name,
                'WaiterConfig': {
                    'Delay': 1,
                    'MaxAttempts': 10
                }
            }
            retry_call(waiter.wait, fkwargs=fkwargs,
                       tries=tries, delay=delay, max_delay=max_delay,
                       backoff=backoff, jitter=jitter)
        except WaiterError as ex:
            logger.error('Failed to get stream while waiting')
            raise StreamNotAvailable('Could not connect to stream') from ex
        except (PartialCredentialsError, NoCredentialsError) as ex:
            logger.error('Credentials missing or incomplete: %s', ex)
            raise ConfigurationError('Credentials missing') from ex
        except ClientError as ex:
            code = ex.response['Error']['Code']
            raise KinesisRequestFailed(f'Last code: {code}') from ex

    def _get_iterator(self) -> str:
        """
        Get a new shard iterator.

        If our position is set, we will start with the record immediately after
        that position. Otherwise, we start at ``start_at`` timestamp.

        Returns
        -------
        str
            The sequence ID of the record on which to start.

        """
        params: Dict[str, Any] = dict(
            StreamName=self.stream_name,
            ShardId=self.shard_id
        )
        if self.position:
            params.update(dict(
                ShardIteratorType='AFTER_SEQUENCE_NUMBER',
                StartingSequenceNumber=self.position
            ))
        elif self.start_type == 'AT_TIMESTAMP' and self.start_at:
            start_at = datetime.strptime(self.start_at, '%Y-%m-%dT%H:%M:%S')
            params.update(dict(
                ShardIteratorType='AT_TIMESTAMP',
                Timestamp=(
                    start_at - datetime.utcfromtimestamp(0)
                ).total_seconds()
            ))
        elif self.start_type == 'TRIM_HORIZON':
            params.update(dict(ShardIteratorType='TRIM_HORIZON'))
        try:
            it: str = self.client.get_shard_iterator(**params)['ShardIterator']
            return it
        except self.client.exceptions.InvalidArgumentException as ex:
            logger.info('Got InvalidArgumentException: %s', str(ex))
            # Iterator may not have come from this stream/shard.
            if self.position is not None:
                self.position = None
                return self._get_iterator()
        raise KinesisRequestFailed('Could not get shard iterator')

    def _checkpoint(self) -> None:
        """
        Checkpoint at the current position.

        The current position is the sequence number of the last record that was
        successfully processed.
        """
        if self.position is not None and self.checkpointer:
            self.checkpointer.checkpoint(self.position)
            logger.debug(f'Set checkpoint at {self.position}')

    def get_records(self, iterator: str, limit: int, tries: int = 5,
                    delay: int = 5, max_delay: Optional[int] = None,
                    backoff: int = 1, jitter: Union[int, Tuple[int, int]] = 0)\
            -> Tuple[str, dict]:
        """Get the next batch of ``limit`` or fewer records."""
        logger.debug(f'Get more records from {iterator}, limit {limit}')
        fkwargs = dict(ShardIterator=iterator, Limit=limit)
        try:
            response = retry_call(self.client.get_records, fkwargs=fkwargs,
                                  exceptions=ClientError, tries=tries,
                                  delay=delay, max_delay=max_delay,
                                  backoff=backoff, jitter=jitter)
        except ClientError as ex:
            code = ex.response['Error']['Code']
            raise KinesisRequestFailed(f'Last code: {code}') from ex
        iterator = response['NextShardIterator']
        return iterator, response

    def _check_timeout(self) -> None:
        """If a processing duration is set, exit if duration is exceeded."""
        if not self.start_time or not self.duration:
            return
        running_for = time.time() - self.start_time
        if running_for > self.duration:
            logger.info(f'Ran for {running_for} seconds; exiting')
            self._checkpoint()
            raise StopProcessing(f'Ran for {running_for} seconds; exiting')

    def process_records(self, start: str) -> Tuple[str, int]:
        """Retrieve and process records starting at ``start``."""
        logger.debug(f'Get more records, starting at {start}')
        processed = 0
        try:
            time.sleep(self.sleep_time)   # Don't get carried away.
            next_start, response = self.get_records(start, self.batch_size,   # type: ignore
                                                    **self.retry_params)
        except Exception as ex:
            self._checkpoint()
            raise StopProcessing('Unhandled exception: %s' % str(ex)) from ex

        logger.debug('Got %i records', len(response['Records']))
        for record in response['Records']:
            self._check_timeout()

            # It is possible that Kinesis will replay the same message several
            # times, especially at the end of the stream. There's no point in
            # replaying the message, so we'll continue on.
            if record['SequenceNumber'] == self.position:
                continue

            self.process_record(record)
            processed += 1

            # Setting the position means that we have successfully
            # processed this record.
            if record['SequenceNumber']:    # Make sure it's set.
                self.position = record['SequenceNumber']
                logger.debug(f'Updated position to {self.position}')
        logger.debug(f'Next start is {next_start}')
        return next_start, processed

    def go(self) -> None:
        """Run the main processing routine."""
        self.client = self.new_client()
        self.get_or_create_stream()

        self.start_time = time.time()
        logger.info(f'Starting processing from position {self.position}'
                    f' on stream {self.stream_name} and shard {self.shard_id}')

        start = self._get_iterator()
        while True:
            start, processed = self.process_records(start)
            if processed > 0:
                self._checkpoint()  # Checkpoint after every batch.
            if start is None:     # Shard is closed.
                logger.error('Shard closed unexpectedly; no new iterator')
                self._checkpoint()
                raise StopProcessing('Could not get a new iterator')
            self._check_timeout()

    def process_record(self, record: dict) -> None:
        """
        Process a single record from the stream.

        Parameters
        ----------
        record : dict

        """
        logger.info(f'Processing record {record["SequenceNumber"]}')
        logger.debug(f'Process record {record}')
        # raise NotImplementedError('Should be implemented by a subclass')


def process_stream(Consumer: type, config: dict,
                   checkpointmanager: Optional[Any] = None,
                   duration: Optional[int] = None,
                   extra: Dict[str, Any] = {}) -> None:
    """
    Configure and run an agent (Kinesis consumer).

    Parameters
    ----------
    Consumer : type
        A class that inherits from :class:`.BaseConsumer`.
    config : dict
        An application config (e.g. a Flask config).
    duration : int
        Time (in seconds) to consume records. If None (default), will
        run "forever".
    extra : kwargs
        Extra keyword arguments passed to the Consumer constructor.

    """
    # By default we use the on-disk checkpoint manager.
    if checkpointmanager is None:
        checkpointmanager = DiskCheckpointManager(
            config['KINESIS_CHECKPOINT_VOLUME'],
            config['KINESIS_STREAM'],
            config['KINESIS_SHARD_ID'],
        )

    with warnings.catch_warnings():     # boto3 is notoriously annoying.
        warnings.simplefilter("ignore")
        start_at = config.get('KINESIS_START_AT')
        start_type = config.get('KINESIS_START_TYPE')
        if not start_type:
            start_type = 'AT_TIMESTAMP'
        if start_type == 'AT_TIMESTAMP' and not start_at:
            start_at = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')

        processor = Consumer(
            config['KINESIS_STREAM'],
            config['KINESIS_SHARD_ID'],
            config['AWS_ACCESS_KEY_ID'],
            config['AWS_SECRET_ACCESS_KEY'],
            config['AWS_REGION'],
            checkpointmanager,
            endpoint=config.get('KINESIS_ENDPOINT', None),
            verify=config.get('KINESIS_VERIFY', 'true') == 'true',
            duration=duration,
            start_type=start_type,
            start_at=start_at,
            tries=config.get('KINESIS_RETRY_TRIES', 5),
            delay=config.get('KINESIS_RETRY_DELAY', 5),
            max_delay=config.get('KINESIS_RETRY_MAX_DELAY', None),
            backoff=config.get('KINESIS_RETRY_BACKOFF', 1),
            jitter=config.get('KINESIS_RETRY_JITTER', 0),
            **extra
        )
        try:
            retry_call(processor.go, exceptions=RestartProcessing)
        except StopProcessing:
            logger.info('Got StopProcessing; stopping.')
            return
