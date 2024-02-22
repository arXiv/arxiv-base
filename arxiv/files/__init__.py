"""
File accessor classes that abstracts the storage and path for each file type.
"""
# The number of classes here are a bit too many. Having a class for each file type is not a good
# design. There is a room for redesign.

import os.path
import shutil
import typing
from abc import abstractmethod
from pathlib import Path
from typing import BinaryIO, TextIO, Any
import urllib.parse
# from typing_extensions import TypedDict

from ..identifier import Identifier

from google.cloud import storage as cloud_storage
from google.cloud.storage.fileio import BlobReader
from .path_mapper import arxiv_id_to_local_orig, local_path_to_blob_key, \
    arxiv_id_to_local_pdf_path, arxiv_id_to_local_paper
import logging

logger = logging.get_logger(__name__)

def make_subpath(path_str: str) -> str:
    """Make a subpath from a path string. If the path string starts with /, remove it."""
    return path_str[1:] if path_str.startswith("/") else path_str


# noinspection Pylint
class ArxivIdentified:
    """Thing identified by arXiv ID"""
    identifier: Identifier

    def __init__(self, identifier: Identifier, **_kwargs: typing.Any):
        self.identifier = identifier
        pass


class AccessorFlavor(ArxivIdentified):
    """Accessor flavor is a mix-in for access."""
    root_dir: str | None

    def __init__(self, identifier: Identifier, **kwargs: typing.Any):
        self.root_dir = kwargs.pop("root_dir", None)
        super().__init__(identifier, **kwargs)
        pass

    @property
    def local_path(self) -> str:
        """ Tarball filename from arXiv ID"""
        return ""

    @property
    def blob_name(self) -> str | None:
        """Turn webnode path to GCP blob name"""
        return local_path_to_blob_key(self.local_path)

    pass


class BaseAccessor(AccessorFlavor):
    """Abstract class for accessing files from GCP and local file system"""

    @abstractmethod
    def exists(self) -> bool:
        """True if the file exists in the storage"""
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def download_to_filename(self, filename: str = "unnamed.bin") -> None:
        """Download the file to the local file system"""
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def upload_from_filename(self, filename: str = "unnamed.bin") -> None:
        """Upload the file to the storage"""
        raise NotImplementedError("Not implemented")

    @abstractmethod
    def download_as_bytes(self, **kwargs: typing.Any) -> bytes:
        """Download the file as bytes"""
        raise NotImplementedError("Not implemented")

    @property
    @abstractmethod
    def canonical_name(self) -> str:
        """Canonical name - URI"""
        raise NotImplementedError("Not implemented")

    @property
    def content_type(self) -> str | None:
        """MIME type of the file, mostly for uploading to GCP"""
        return None

    @abstractmethod
    def open(self, **kwargs: typing.Any) -> BlobReader | BinaryIO:
        """Open the srorage (file or GCP blob) and return the file-ish object"""
        raise NotImplementedError("Not implemented")

    @property
    def bytesize(self) -> typing.Optional[int]:
        """Object byte size, if applicable"""
        return None

    @property
    @abstractmethod
    def basename(self) -> str:
        """Base name of the file"""
        raise NotImplementedError("Not implemented")

    pass


# noinspection Pylint
class GCPStorage:
    """GCP storage client and bucket"""
    client: cloud_storage.Client
    bucket_name: str
    bucket: cloud_storage.Bucket

    def __init__(self, client: cloud_storage.Client, bucket_name: str):
        self.client = client
        self.bucket_name = bucket_name
        self.bucket = self.client.bucket(self.bucket_name)


class GCPBlobAccessor(BaseAccessor):
    """GCP Blob accessor for a given arXiv ID. This is an abstract class.
    You need to implement to_blob_name property in the subclass.
    """
    gcp_storage: GCPStorage
    blob: cloud_storage.Blob

    def __init__(self, identifier: Identifier, **kwargs: typing.Any):
        self.gcp_storage = kwargs.pop("storage")
        super().__init__(identifier, **kwargs)
        if self.blob_name is None:
            raise ValueError("blob_name is None")
        self.blob = self.bucket.blob(self.blob_name)

    def download_to_filename(self, filename: str = "unnamed.bin") -> None:
        self.blob.download_to_filename(filename)

    def upload_from_filename(self, filename: str = "unnamed.bin") -> None:
        logger.debug(f"upload_from_filename: {filename} to {self.blob_name}")
        self.blob.upload_from_filename(filename, content_type=self.content_type)

    def download_as_bytes(self, **kwargs: typing.Any) -> bytes:
        return self.blob.download_as_bytes(**kwargs)  # type: ignore

    @property
    def bucket(self) -> cloud_storage.Bucket:
        """GCP bucket"""
        return self.gcp_storage.bucket

    def exists(self) -> bool:
        return self.blob.exists(client=self.gcp_storage.client)  # type: ignore

    @property
    def basename(self) -> str:
        if self.blob_name is None:
            raise ValueError("blob_name is None")
        return os.path.basename(urllib.parse.urlparse(self.blob_name).path)

    @property
    def canonical_name(self) -> str:
        return f'gs://{self.gcp_storage.bucket_name}/{self.blob_name}'

    def open(self, **kwargs: Any) -> BlobReader | BinaryIO | TextIO:
        return self.blob.open(**kwargs)

    @property
    def bytesize(self) -> typing.Optional[int]:
        if self.blob.exists(client=self.gcp_storage.client):
            self.blob.reload()
            return self.blob.size  # type: ignore
        return None

    pass


class LocalFileAccessor(BaseAccessor):
    """Local file accessor for a given arXiv ID. This is an abstract class."""

    def __init__(self, identifier: Identifier, **kwargs: Any):
        super().__init__(identifier, **kwargs)
        pass

    def download_to_filename(self, filename: str = "unnamed.bin") -> None:
        local_path = self.local_path
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        shutil.copyfile(self.local_path, filename)

    def upload_from_filename(self, filename: str = "unnamed.bin") -> None:
        local_path = self.local_path
        os.makedirs(os.path.dirname(local_path), exist_ok=True)
        shutil.copyfile(filename, local_path)

    def download_as_bytes(self, **kwargs: Any) -> bytes:
        with open(self.local_path, 'rb') as fd:
            return bytes(fd.read())

    def exists(self) -> bool:
        return Path(self.local_path).exists()

    @property
    def basename(self) -> str:
        return os.path.basename(self.local_path)

    @property
    def canonical_name(self) -> str:
        return f'file://{self.local_path}'

    def open(self, **kwargs: typing.Any) -> BlobReader | BinaryIO | TextIO:
        mode: str = kwargs.pop("mode", "rb")
        return open(self.local_path, mode=mode)

    @property
    def bytesize(self) -> typing.Optional[int]:
        po = Path(self.local_path)
        if po.exists():
            return po.stat().st_size
        return None

    @property
    def blob_name(self) -> str | None:
        return None

    pass


def merge_path(root_dir: str | None, local_path: str) -> str:
    """Merge root_dir and local_path"""
    if root_dir:
        return os.path.join(root_dir, make_subpath(local_path))
    return local_path


class VersionedFlavor(AccessorFlavor):
    """Versioned flavor needs to look at two places to decide the path. If it is latest,
    it is in arxiv_id_to_local_paper() (aka under /ftp), and else  arxiv_id_to_local_orig()
    (aka under /data/orig).
    """

    def __init__(self, arxiv_id: Identifier, **kwargs: typing.Any):
        latest = kwargs.pop("latest", None)
        if latest is None:
            raise ValueError("latest is not set. It must be True or False.")
        self.path_mapper = arxiv_id_to_local_paper if latest else arxiv_id_to_local_orig
        super().__init__(arxiv_id, **kwargs)
        pass


class TarballFlavor(VersionedFlavor):
    """Tarball flavor"""

    @property
    def local_path(self) -> str:
        """ Tarball filename from arXiv ID"""
        return merge_path(self.root_dir, self.path_mapper(self.identifier, extent=".tar.gz"))

    pass


class AbsFlavor(VersionedFlavor):
    """GCP abstract text blob accessor for a given arXiv ID."""

    @property
    def local_path(self) -> str:
        return merge_path(self.root_dir, self.path_mapper(self.identifier, extent=".abs"))

    pass


class PDFFlavor(AccessorFlavor):
    """GCP PDF blob accessor for a given arXiv ID."""

    @property
    def local_path(self) -> str:
        return merge_path(self.root_dir, arxiv_id_to_local_pdf_path(self.identifier))

    pass


class OutcomeFlavor(AccessorFlavor):
    """GCP pdfgen outcome blob accessor for a given arXiv ID.
    Outcome blob is a tarball containing the output files from running pdflatex except actual PDF.
    """

    @property
    def local_path(self) -> str:
        # If outcome is at webnode, this is where it would be - next to the PDF.
        return merge_path(self.root_dir,
                          arxiv_id_to_local_pdf_path(self.identifier, extent=".outcome.tar.gz"))

    pass


class LocalTarballAccessor(LocalFileAccessor, TarballFlavor):
    """Local tarball accessor for a given arXiv ID."""


class LocalPDFAccessor(LocalFileAccessor, PDFFlavor):
    """Local PDF accessor for a given arXiv ID."""


class LocalAbsAccessor(LocalFileAccessor, AbsFlavor):
    """Local abstract text accessor for a given arXiv ID."""


class LocalOutcomeAccessor(LocalFileAccessor, OutcomeFlavor):
    """Local outcome accessor for a given arXiv ID."""


class GCPTarballAccessor(GCPBlobAccessor, TarballFlavor):
    """GCP tarball accessor for a given arXiv ID."""


class GCPPDFAccessor(GCPBlobAccessor, PDFFlavor):
    """GCP PDF accessor for a given arXiv ID."""


class GCPAbsAccessor(GCPBlobAccessor, AbsFlavor):
    """GCP abstract text accessor for a given arXiv ID."""
    pass


class GCPOutcomeAccessor(GCPBlobAccessor, OutcomeFlavor):
    """GCP outcome accessor for a given arXiv ID."""
    pass
