"""Tests for :class:`.BaseConsumer`."""

from unittest import TestCase, mock
import time
from botocore.exceptions import BotoCoreError, WaiterError, ClientError

from ..consumer import BaseConsumer, CheckpointError, StopProcessing, \
    KinesisRequestFailed, ConfigurationError, StreamNotAvailable, \
    process_stream, RestartProcessing


import logging
logging.getLogger('integration.kinesis.consumer').setLevel(logging.WARNING)


class TestBaseConsumer(TestCase):
    """Test :class:`.BaseConsumer` behavior and public methods."""

    def setUp(self):
        """Create a mock checkpointer."""
        self.checkpointer = mock.MagicMock()
        self.checkpointer.position = None

    @mock.patch('boto3.Session')
    def test_go(self, mock_session_factory):
        """On go, consumer should wait for stream to be available."""
        mock_client = mock.MagicMock()
        mock_waiter = mock.MagicMock()
        mock_client.get_waiter.return_value = mock_waiter
        mock_client.get_records.side_effect = StopProcessing
        mock_session_factory.return_value = \
            mock.MagicMock(client=mock.MagicMock(return_value=mock_client))

        consumer = BaseConsumer('foo', '1', 'a1b2c3d4', 'qwertyuiop',
                                'us-east-1', self.checkpointer, delay=0)
        consumer.sleep_time = 0     # Don't wait.
        try:
            consumer.go()
        except StopProcessing:
            pass    # This was intentional; we needed to stop processing.
        except Exception:
            self.fail('If the waiter returns without an exception, no'
                      ' exception should be raised.')
        self.assertEqual(mock_waiter.wait.call_count, 1,
                         "A boto3 waiter should be used")

    @mock.patch('boto3.Session')
    def test_go_stream_not_available(self, mock_session_factory):
        """If the stream is not available, should raise an exception."""
        mock_client = mock.MagicMock()
        mock_waiter = mock.MagicMock()

        def raise_waiter_error(*a, **k):
            raise WaiterError('', {}, {})

        mock_waiter.wait.side_effect = raise_waiter_error
        mock_client.get_waiter.return_value = mock_waiter
        mock_session_factory.return_value = \
            mock.MagicMock(client=mock.MagicMock(return_value=mock_client))
        consumer = BaseConsumer('foo', '1', 'a1b2c3d4', 'qwertyuiop',
                                'us-east-1', self.checkpointer, delay=0)
        consumer.sleep_time = 0     # Don't wait.
        with self.assertRaises(StreamNotAvailable):
            consumer.go()

    @mock.patch('boto3.Session')
    def test_iteration(self, mock_session_factory):
        """Test iteration behavior."""
        mock_client = mock.MagicMock()
        mock_session_factory.return_value = \
            mock.MagicMock(client=mock.MagicMock(return_value=mock_client))
        mock_client.get_records.return_value = {
            'Records': [
                {'SequenceNumber': str(i)} for i in range(10)
            ],
            'NextShardIterator': '10'
        }
        consumer = BaseConsumer('foo', '1', 'a1b2c3d4', 'qwertyuiop',
                                'us-east-1', self.checkpointer)
        consumer.sleep_time = 0     # Don't wait.
        consumer.client = consumer.new_client()

        next_start, processed = consumer.process_records('0')
        self.assertGreater(mock_client.get_records.call_count, 0)
        self.assertEqual(processed, 10)
        self.assertEqual(next_start, '10', "Should return NextShardIterator")

    @mock.patch('boto3.Session')
    def test_process_records_until_shard_closes(self, mock_session_factory):
        """Should call GetRecords until no next iterator is available."""
        mock_client = mock.MagicMock()
        mock_session_factory.return_value = \
            mock.MagicMock(client=mock.MagicMock(return_value=mock_client))
        mock_client.get_shard_iterator.return_value = {'ShardIterator': '1'}

        def get_records(**kwargs):
            start = int(kwargs['ShardIterator'])
            end = start + int(kwargs['Limit'])
            if start > 100:
                return {'Records': [], 'NextShardIterator': None}
            return {
                'Records': [
                    {'SequenceNumber': str(i)} for i in range(start, end)
                ],
                'NextShardIterator': str(end + 1)
            }

        mock_client.get_records.side_effect = get_records

        batch_size = 50
        consumer = BaseConsumer('foo', '1', 'a1b2c3d4', 'qwertyuiop',
                                'us-east-1', self.checkpointer,
                                batch_size=batch_size)
        consumer.sleep_time = 0     # Don't wait.
        with self.assertRaises(StopProcessing):
            consumer.go()
        self.assertEqual(mock_client.get_records.call_count,
                         (100/batch_size) + 1,
                         "Should call Kinesis GetRecords until no iterator"
                         " is returned.")

    @mock.patch('boto3.Session')
    def test_process_records_with_clienterror(self, mock_session_factory):
        """Should try to checkpoint before exiting."""
        mock_client = mock.MagicMock()
        mock_session_factory.return_value = \
            mock.MagicMock(client=mock.MagicMock(return_value=mock_client))
        mock_client.get_shard_iterator.return_value = {'ShardIterator': '1'}

        def raise_client_error(*args, **kwargs):
            raise ClientError({'Error': {'Code': 'foo'}}, {})

        mock_client.get_records.side_effect = raise_client_error

        batch_size = 50
        consumer = BaseConsumer('foo', '1', 'a1b2c3d4', 'qwertyuiop',
                                'us-east-1', self.checkpointer,
                                batch_size=batch_size, delay=0)
        consumer.sleep_time = 0     # Don't wait.
        consumer.position = 'fooposition'
        try:
            consumer.go()
        except Exception:
            pass
        self.assertEqual(self.checkpointer.checkpoint.call_count, 1)

    @mock.patch('boto3.Session')
    def test_start_from_timestamp(self, mock_session_factory):
        """Consumer is initialized with start_type 'AT_TIMESTAMP'."""
        mock_client = mock.MagicMock()
        mock_session_factory.return_value = \
            mock.MagicMock(client=mock.MagicMock(return_value=mock_client))
        mock_client.get_shard_iterator.return_value = {'ShardIterator': '1'}

        consumer = BaseConsumer('foo', '1', 'a1b2c3d4', 'qwertyuiop',
                                'us-east-1', self.checkpointer,
                                start_type='AT_TIMESTAMP')
        consumer.sleep_time = 0     # Don't wait.
        consumer.client = consumer.new_client()
        consumer._get_iterator()
        args, kwargs = mock_client.get_shard_iterator.call_args
        self.assertEqual(kwargs['ShardIteratorType'], 'AT_TIMESTAMP')
        self.assertIn('Timestamp', kwargs)

    @mock.patch('boto3.Session')
    def test_start_from_position(self, mock_session_factory):
        """Consumer is initialized with start_type 'AT_TIMESTAMP'."""
        mock_client = mock.MagicMock()
        mock_session_factory.return_value = \
            mock.MagicMock(client=mock.MagicMock(return_value=mock_client))
        mock_client.get_shard_iterator.return_value = {'ShardIterator': '1'}

        consumer = BaseConsumer('foo', '1', 'a1b2c3d4', 'qwertyuiop',
                                'us-east-1', self.checkpointer,
                                start_type='AT_TIMESTAMP')
        consumer.sleep_time = 0     # Don't wait.
        consumer.client = consumer.new_client()
        consumer.position = 'fooposition'
        consumer._get_iterator()
        args, kwargs = mock_client.get_shard_iterator.call_args
        self.assertEqual(kwargs['ShardIteratorType'], 'AFTER_SEQUENCE_NUMBER')
        self.assertEqual(kwargs['StartingSequenceNumber'], 'fooposition')

    @mock.patch('boto3.Session')
    def test_start_from_trim_horizon(self, mock_session_factory):
        """Consumer is initialized with start_type 'AT_TIMESTAMP'."""
        mock_client = mock.MagicMock()
        mock_session_factory.return_value = \
            mock.MagicMock(client=mock.MagicMock(return_value=mock_client))
        mock_client.get_shard_iterator.return_value = {'ShardIterator': '1'}

        consumer = BaseConsumer('foo', '1', 'a1b2c3d4', 'qwertyuiop',
                                'us-east-1', self.checkpointer,
                                start_type='TRIM_HORIZON')
        consumer.sleep_time = 0     # Don't wait.
        consumer.client = consumer.new_client()
        consumer._get_iterator()
        args, kwargs = mock_client.get_shard_iterator.call_args
        self.assertEqual(kwargs['ShardIteratorType'], 'TRIM_HORIZON')
        self.assertNotIn('StartingSequenceNumber', kwargs)


class TestProcessStream(TestCase):
    """Tests for :func:`.process_stream`."""

    def setUp(self):
        """Define a testing config."""
        self.config = {
            'KINESIS_STREAM': 'fooStream',
            'KINESIS_SHARD_ID': 'shard-0000000',
            'AWS_ACCESS_KEY_ID': 'ack',
            'AWS_SECRET_ACCESS_KEY': 'qwerty',
            'AWS_REGION': 'su-tsae-9'
        }

    @mock.patch('boto3.Session')
    def test_process_stream(self, mock_session_factory):
        """Run :func:`.process_stream` with a vanilla config."""
        mock_client = mock.MagicMock()
        mock_session_factory.return_value = \
            mock.MagicMock(client=mock.MagicMock(return_value=mock_client))
        mock_client.get_shard_iterator.return_value = {'ShardIterator': '1'}
        mock_client.get_records.return_value = {
            "Records": [
                {'SequenceNumber': '1', 'Data': 'bat'},
                {'SequenceNumber': '2', 'Data': 'abt'},
                {'SequenceNumber': '3', 'Data': 'tab'},
                {'SequenceNumber': '4', 'Data': 'bta'},
            ],
            "NextShardIterator": "5"
        }

        class FooConsumer(BaseConsumer):
            def __init__(self, *args, **kwargs):
                super(FooConsumer, self).__init__(*args, **kwargs)
                self.sleep_time = 0.01

            process_record = mock.MagicMock()

        class FooCheckpointer(object):
            def __init__(self):
                self.position = None

            def checkpoint(self, position):
                self.position = position
        start = time.time()
        process_stream(FooConsumer, self.config, FooCheckpointer(), 2)
        self.assertGreaterEqual(time.time() - start, 2,
                                "Should run for at least 2 seconds")
        self.assertGreater(FooConsumer.process_record.call_count, 0,
                           "Should be called at least several times")

    @mock.patch('boto3.Session')
    def test_restart_processing(self, mock_session_factory):
        """The record processor raises :class:`.RestartProcessing`."""
        mock_client = mock.MagicMock()
        mock_session_factory.return_value = \
            mock.MagicMock(client=mock.MagicMock(return_value=mock_client))
        mock_client.get_shard_iterator.return_value = {'ShardIterator': '1'}
        mock_client.get_records.return_value = {
            "Records": [
                {'SequenceNumber': '1', 'Data': 'bat'},
                {'SequenceNumber': '2', 'Data': 'abt'},
                {'SequenceNumber': '3', 'Data': 'tab'},
                {'SequenceNumber': '4', 'Data': 'bta'},
            ],
            "NextShardIterator": "5"
        }

        class FooConsumer(BaseConsumer):
            def __init__(self, *args, **kwargs):
                super(FooConsumer, self).__init__(*args, **kwargs)
                self.sleep_time = 0.01

            go = mock.MagicMock(side_effect=[RestartProcessing,
                                             RestartProcessing,
                                             StopProcessing])

        class FooCheckpointer(object):
            def __init__(self):
                self.position = None

            def checkpoint(self, position):
                self.position = position

        process_stream(FooConsumer, self.config, FooCheckpointer(), 2)
        self.assertEqual(FooConsumer.go.call_count, 3,
                         'Should be retried')
