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
from datetime import datetime, timedelta
import os
from typing import Any, Optional, Tuple, Generator, Callable, Dict, Union
from contextlib import contextmanager
import signal
import warnings

import boto3
from botocore.exceptions import WaiterError, NoCredentialsError, \
    PartialCredentialsError, BotoCoreError, ClientError

from arxiv.base import logging
from .exceptions import CheckpointError, StreamNotAvailable, StopProcessing, \
    KinesisRequestFailed, ConfigurationError

logger = logging.getLogger(__name__)
logger.propagate = False

NOW = datetime.now().strftime('%Y-%m-%dT%H:%M:%S')


def retry(retries: int = 5, wait: int = 5) -> Callable:
    """
    Decorator factory for retrying Kinesis calls.

    Parameters
    ----------
    retries : int
        Number of times to retry before failing.
    wait : int
        Number of seconds to wait between retries.

    Returns
    -------
    function
        A decorator that retries the decorated func ``retries`` times before
        raising :class:`.KinesisRequestFailed`.

    """
    __retries = retries

    def decorator(func: Callable) -> Callable:
        """Retry the decorated func on ClientErrors up to ``retries`` times."""
        _retries = __retries

        def inner(*args, **kwargs) -> Any:  # type: ignore
            retries = _retries
            while retries > 0:
                try:
                    return func(*args, **kwargs)
                except ClientError as e:
                    code = e.response['Error']['Code']
                    logger.error('Caught ClientError %s, retrying', code)
                    time.sleep(wait)
                    retries -= 1
            raise KinesisRequestFailed('Max retries; last code: {code}')
        return inner
    return decorator


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
            except Exception as e:   # The containing path doesn't exist.
                raise ValueError(f'Could not use {self.file_path}') from e

        with open(self.file_path) as f:
            position = f.read()
        self.position = position if position else None

    def checkpoint(self, position: str) -> None:
        """Checkpoint at ``position``."""
        try:
            with open(self.file_path, 'w') as f:
                f.write(position)
            self.position = position
        except Exception as e:
            raise CheckpointError('Could not checkpoint') from e


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
                 start_at: str = NOW) -> None:
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
        self.start_time = None
        self.back_off = back_off
        self.batch_size = batch_size
        self.sleep_time = 5
        self.start_at = start_at
        self.start_type = start_type
        logger.info(f'Got start_type={start_type} and start_at={start_at}')

        if not self.stream_name or not self.shard_id:
            logger.info(
                'No stream indicated; making no attempt to connect to Kinesis'
            )
            return

        logger.info(f'Getting a new connection to Kinesis at {endpoint}'
                    f' in region {region}, with SSL verification={verify}')
        params = dict(
            endpoint_url=endpoint,
            verify=verify,
            region_name=region
        )
        # Only add these if they are set/truthy. This allows us to use a
        # shared credentials file via an environment variable.
        if access_key and secret_key:
            params.update(dict(
                aws_access_key_id=access_key,
                aws_secret_access_key=secret_key
            ))
        logger.debug('New client with parameters: %s', params)
        self.client = boto3.client('kinesis', **params)

        logger.info(f'Waiting for {self.stream_name} to be available')
        try:
            self.wait_for_stream()
        except (KinesisRequestFailed, StreamNotAvailable):
            logger.info('Could not connect to stream; attempting to create')
            self.client.create_stream(
                StreamName=self.stream_name,
                ShardCount=1
            )
            logger.info(f'Created; waiting for {self.stream_name} again')
            self.wait_for_stream()

        # Intercept SIGINT and SIGTERM so that we can checkpoint before exit.
        self.exit = False
        signal.signal(signal.SIGINT, self.stop)
        signal.signal(signal.SIGTERM, self.stop)
        logger.info('Ready to start')

    def stop(self, signal: int, frame: Any) -> None:
        """Set exit flag for a graceful stop."""
        logger.error(f'Received signal {signal}')
        self._checkpoint()
        logger.error('Done')
        raise StopProcessing(f'Received signal {signal}')

    @retry(5, 10)
    def wait_for_stream(self) -> None:
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
            waiter.wait(
                StreamName=self.stream_name,
                Limit=1,
                ExclusiveStartShardId=self.shard_id
            )
        except WaiterError as e:
            logger.error('Failed to get stream while waiting')
            raise StreamNotAvailable('Could not connect to stream') from e
        except (PartialCredentialsError, NoCredentialsError) as e:
            logger.error('Credentials missing or incomplete: %s', e.msg)
            raise ConfigurationError('Credentials missing') from e

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
        except self.client.exceptions.InvalidArgumentException as e:
            logger.info('Got InvalidArgumentException: %s', str(e))
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

    @retry(retries=10, wait=5)
    def get_records(self, iterator: str, limit: int) -> Tuple[str, dict]:
        """Get the next batch of ``limit`` or fewer records."""
        logger.debug(f'Get more records from {iterator}, limit {limit}')
        response = self.client.get_records(ShardIterator=iterator,
                                           Limit=limit)
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
            next_start, response = self.get_records(start, self.batch_size)
        except Exception as e:
            self._checkpoint()
            raise StopProcessing('Unhandled exception: %s' % str(e)) from e

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
        """Main processing routine."""
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
                   duration: Optional[int] = None) -> None:
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
            start_at=start_at
        )
        try:
            processor.go()
        except StopProcessing:
            logger.info('Got StopProcessing; stopping.')
            return
