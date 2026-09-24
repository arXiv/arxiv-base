"""Paper ids, bucket keys and per-month DB queries shared by the file checks."""

import re
from collections.abc import Iterator
from dataclasses import dataclass
from datetime import UTC, date, datetime

from arxiv.taxonomy.definitions import ARCHIVES
from sqlalchemy import Connection, bindparam, text

NEW_ID_START = 200704  # first yyyymm of 2101.12345-style ids

_OLD_ARCHIVES = sorted(a.id for a in ARCHIVES.values() if a.start_date < date(2007, 4, 1) and a.id != "arxiv")

_KEY_RE = [
    re.compile(r"(?:^|/)arxiv/papers/(\d{4})/(\d{4}\.\d{4,5})(?:v(\d+))?\.([a-z.]+)$"),
    re.compile(r"(?:^|/)([a-z-]+)/papers/(\d{4})/(\d{7})(?:v(\d+))?\.([a-z.]+)$"),
]


def split_id(paper_id: str) -> tuple[str, str, str]:
    """-> (archive dir, yymm, filename stem): hep-th/9901001 -> (hep-th, 9901, 9901001)."""
    if "/" in paper_id:
        archive, num = paper_id.split("/", 1)
        return archive, num[:4], num
    return "arxiv", paper_id[:4], paper_id


def paper_dir(area: str, paper_id: str) -> str:
    archive, yymm, _ = split_id(paper_id)
    return f"{area}/{archive}/papers/{yymm}/"


def paper_key(area: str, paper_id: str, ext: str, version: int | None = None) -> str:
    stem = split_id(paper_id)[2] + (f"v{version}" if version else "")
    return f"{paper_dir(area, paper_id)}{stem}.{ext}"


@dataclass(frozen=True)
class ParsedKey:
    paper_id: str
    version: int | None
    ext: str


def parse_key(key: str) -> ParsedKey | None:
    """Parse ftp/orig paper file keys; None if the name is not a paper file."""
    if m := _KEY_RE[0].search(key):
        _, pid, v, ext = m.groups()
        return ParsedKey(pid, int(v) if v else None, ext)
    if m := _KEY_RE[1].search(key):
        archive, _, num, v, ext = m.groups()
        return ParsedKey(f"{archive}/{num}", int(v) if v else None, ext)
    return None


def yyyymm(yymm: str) -> int:
    return int(("19" if int(yymm) >= 9000 else "20") + yymm)


def all_yymms(today: date | None = None) -> list[str]:
    today = today or datetime.now(UTC).date()
    out, y, m = [], 1991, 8
    while (y, m) <= (today.year, today.month):
        out.append(f"{y % 100:02d}{m:02d}")
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)
    return out


def parse_yymms(spec: str | None) -> list[str]:
    """'2101,2103-2105' -> ['2101', '2103', '2104', '2105']; None -> all months."""
    months = all_yymms()
    if not spec:
        return months
    out: list[str] = []
    for part in spec.split(","):
        lo, _, hi = part.strip().partition("-")
        if lo not in months or (hi and hi not in months):
            raise ValueError(f"bad yymm '{part}'")
        out += months[months.index(lo) : months.index(hi or lo) + 1]
    return out


def month_id_clause(yymm: str) -> tuple[str, dict]:
    """SQL condition on paper_id selecting the ids of one month (index friendly)."""
    if yyyymm(yymm) >= NEW_ID_START:
        return "paper_id LIKE :p0", {"p0": f"{yymm}.%"}
    params = {f"p{i}": f"{a}/{yymm}%" for i, a in enumerate(_OLD_ARCHIVES)}
    return "(" + " OR ".join(f"paper_id LIKE :{k}" for k in params) + ")", params


@dataclass
class Version:
    paper_id: str
    document_id: int
    version: int
    is_current: bool
    is_withdrawn: bool
    abs_categories: str | None


def month_versions(conn: Connection, yymm: str) -> list[Version]:
    where, params = month_id_clause(yymm)
    rows = conn.execute(
        text(
            "SELECT paper_id, document_id, version, is_current, is_withdrawn, abs_categories "
            f"FROM arXiv_metadata WHERE {where}"
        ),
        params,
    )
    return [Version(r[0], r[1], r[2], bool(r[3]), bool(r[4]), r[5]) for r in rows]


def in_category(conn: Connection, document_ids: list[int]) -> Iterator[tuple[int, str, str, bool]]:
    """(document_id, archive, subject_class, is_primary) rows."""
    q = text(
        "SELECT document_id, archive, subject_class, is_primary FROM arXiv_in_category WHERE document_id IN :ids"
    ).bindparams(bindparam("ids", expanding=True))
    for i in range(0, len(document_ids), 1000):
        for r in conn.execute(q, {"ids": document_ids[i : i + 1000]}):
            yield r[0], r[1], r[2] or "", bool(r[3])
