"""Minimal read-only view of the data bucket (or a local copy of it).

Keys use the bucket layout: ``ftp/…``, ``orig/…``, ``ps_cache/…``, ``txt/…``.

ponytail: not `arxiv.files.object_store` because checks need recursive
listing and directory (delimiter) listing, which its `LocalObjectStore` lacks.
"""

import shutil
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import BinaryIO, Protocol


@dataclass(frozen=True)
class Obj:
    key: str
    size: int
    updated: datetime  # tz-aware UTC


class Store(Protocol):
    def objects(self, prefix: str) -> Iterator[Obj]:
        """All objects whose key starts with `prefix` (recursive)."""
        ...

    def list_dir(self, prefix: str) -> tuple[list[str], list[Obj]]:
        """Immediate sub-prefixes (ending in /) and objects under `prefix`/."""
        ...

    def get(self, key: str) -> Obj | None: ...

    def open(self, key: str) -> BinaryIO: ...

    def download(self, key: str, dest: Path) -> None: ...


class GcsStore:
    def __init__(self, bucket_name: str, connections: int = 32):
        from google.cloud import storage
        from requests.adapters import HTTPAdapter

        client = storage.Client()
        # default pool is 10 connections; the checks read with many threads
        client._http.mount("https://", HTTPAdapter(pool_connections=connections, pool_maxsize=connections))
        self.bucket = client.bucket(bucket_name)

    @staticmethod
    def _obj(blob) -> Obj:
        return Obj(blob.name, blob.size or 0, blob.updated)

    def objects(self, prefix: str) -> Iterator[Obj]:
        for blob in self.bucket.list_blobs(prefix=prefix, fields="items(name,size,updated),nextPageToken"):
            yield self._obj(blob)

    def list_dir(self, prefix: str) -> tuple[list[str], list[Obj]]:
        it = self.bucket.list_blobs(prefix=prefix, delimiter="/")
        objs = [self._obj(b) for b in it]  # consuming pages fills it.prefixes
        return sorted(it.prefixes), objs

    def get(self, key: str) -> Obj | None:
        blob = self.bucket.get_blob(key)
        return self._obj(blob) if blob else None

    def open(self, key: str) -> BinaryIO:
        return self.bucket.blob(key).open("rb")

    def download(self, key: str, dest: Path) -> None:
        self.bucket.blob(key).download_to_filename(str(dest))


class LocalStore:
    """A directory laid out like the bucket, for tests and local runs."""

    def __init__(self, root: str | Path):
        self.root = Path(root)

    def _obj(self, path: Path) -> Obj:
        st = path.stat()
        return Obj(path.relative_to(self.root).as_posix(), st.st_size, datetime.fromtimestamp(st.st_mtime, tz=UTC))

    def objects(self, prefix: str) -> Iterator[Obj]:
        base = self.root / prefix
        parent = base if prefix.endswith("/") else base.parent
        if not parent.is_dir():
            return
        for path in sorted(parent.rglob("*")):
            if path.is_file() and path.relative_to(self.root).as_posix().startswith(prefix):
                yield self._obj(path)

    def list_dir(self, prefix: str) -> tuple[list[str], list[Obj]]:
        base = self.root / prefix
        if not base.is_dir():
            return [], []
        entries = sorted(base.iterdir())
        dirs = [f"{prefix}{p.name}/" for p in entries if p.is_dir()]
        return dirs, [self._obj(p) for p in entries if p.is_file()]

    def get(self, key: str) -> Obj | None:
        path = self.root / key
        return self._obj(path) if path.is_file() else None

    def open(self, key: str) -> BinaryIO:
        return (self.root / key).open("rb")

    def download(self, key: str, dest: Path) -> None:
        shutil.copyfile(self.root / key, dest)
