"""Exceptions raised by :class:`.BaseConsumer`."""


class CheckpointError(RuntimeError):
    """Checkpointing failed."""


class StreamNotAvailable(RuntimeError):
    """Could not find or connect to the stream."""


class KinesisRequestFailed(RuntimeError):
    """Raised when a Kinesis request failed permanently."""


class StopProcessing(RuntimeError):
    """Gracefully stopped processing upon unrecoverable error."""


class ConfigurationError(RuntimeError):
    """There was a problem with the configuration."""


class RestartProcessing(RuntimeError):
    """Something happened that requires a restart."""
