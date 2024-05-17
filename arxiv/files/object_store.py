"""The object store service to access local or cloud files."""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, \
    Literal, Tuple, Iterator

from google.cloud.storage.blob import Blob
from google.cloud.storage.bucket import Bucket
from google.cloud.storage.retry import DEFAULT_RETRY

from . import FileObj

GCS_RETRY = DEFAULT_RETRY \
    .with_deadline(12) \
    .with_delay(0.25, 2.5)

class ObjectStore(ABC):
    """ABC for an object store."""

    @abstractmethod
    def to_obj(self, key: str) -> FileObj:
        """Gets a `FileObj` given a key."""
        pass

    @abstractmethod
    def list(self, dir: str) -> Iterable[FileObj]:
        """Gets a listing similar to returned by `Client.list_blobs()`

        `dir` should end with a /
        """
        pass

    @abstractmethod
    def status(self) -> Tuple[Literal["GOOD", "BAD"], str]:
        """Indicates the health of the service.

        Returns a tuple of either ("GOOD",'') or ("BAD","Some human
        readable message")

        The human readable message might be displayed publicly so do not
        put sensitive information in it.
        """
        pass

##########################################################################
###### Local Object Store
##########################################################################

from . import FileDoesNotExist, FileObj, LocalFileObj

class LocalObjectStore(ObjectStore):
    """ObjectStore that uses local FS and Path."""
    def __init__(self, prefix:str):
        if not prefix:
            raise ValueError("Must have a prefix")
        if not prefix.endswith('/'):
            prefix = prefix + "/"

        self.prefix = prefix

    def to_obj(self,  key:str) -> FileObj:
        """Gets a `LocalFileObj` from local file system."""
        item = Path(self.prefix + key)
        if not item or not item.exists():
            return FileDoesNotExist(self.prefix + key)
        else:
            return LocalFileObj(Path(item))


    def list(self, key: str) -> Iterator[FileObj]:
        """Gets a listing similar to what would be returned by
        `Client.list_blobs()`

        if `key` ends with / it does a dir listing, other wise it does a
        `prefix` + `key` * listing.
        """
        if key.endswith("/"):
            return (LocalFileObj(item) for item in Path(self.prefix+key).glob("*"))
        else:
            parent, file = Path(self.prefix + key).parent, Path(self.prefix + key).name
            return (LocalFileObj(item) for item in Path(parent).glob(f"{file}*"))

    def status(self) -> Tuple[Literal["GOOD", "BAD"], str]:
        if Path(self.prefix).exists():
            return ("GOOD", "")
        else:
            return ("BAD", "Local storage path doesn't exist")

    def __repr__(self) -> str:
        return self.__str__()

    def __str__(self) -> str:
        return f"<LocalObjectStore {self.prefix}>"
    
    
##########################################################################
###### GCS Object Store
##########################################################################

FileObj.register(Blob)

class GsObjectStore(ObjectStore):
    def __init__(self, bucket: Bucket):
        if not bucket:
            raise ValueError("Must set a bucket")
        self.bucket = bucket

    def to_obj(self, key: str) -> FileObj:
        """Gets the `Blob` fom google-cloud-storage.

        Returns `FileDoesNotExist` if there is no object at the key.
        """
        try:
            blob = self.bucket.get_blob(key, retry=GCS_RETRY)
        except:
            blob = None
        if not blob:
            return FileDoesNotExist("gs://" + self.bucket.name + '/' + key)
        else:
            return blob  # type: ignore

    def list(self, prefix: str) -> Iterator[FileObj]:
        """Gets listing of keys with prefix.

        `prefix` should be just a path to a file name. Example:
        'ps_cache/arxiv/pdf/1212/1212.12345' or
        'ftp/cs/papers/0012/0012007'.
        """
        try:
            return self.bucket.client.list_blobs(self.bucket, prefix=prefix)  # type: ignore
        except Exception as e:
            raise RuntimeError (f'.list failed on gs://{self.bucket.name}/{prefix}') from e

    def status(self) -> Tuple[Literal["GOOD", "BAD"], str]:
        """Gets if bucket can be read."""
        if self.bucket.exists():
            return ("GOOD", '')
        else:
            return ("BAD", 'bucket does not exist or API down')
