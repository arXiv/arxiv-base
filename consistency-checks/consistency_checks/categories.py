"""Categories-line model, port of arxiv-lib arXiv::Categories.

Only what the checks need: parse/serialize, canonicalize() and
is_valid_for_id(). Alias pairs come from arxiv.taxonomy.
"""

import re

from arxiv.taxonomy.definitions import ARCHIVES_SUBSUMED, CATEGORIES, CATEGORY_ALIASES

from .legacy_categories import FUNCT_AN_TO_OA, KNOWN_BAD_PRIMARY, LEGACY_ARCHIVE_AS_PRIMARY, LEGACY_ARCHIVE_AS_SECONDARY

EQUIV = CATEGORY_ALIASES  # alias -> canonical, e.g. cs.SY -> eess.SY
INV_EQUIV = {v: k for k, v in EQUIV.items()}
_LEGACY = set(LEGACY_ARCHIVE_AS_PRIMARY) | set(LEGACY_ARCHIVE_AS_SECONDARY)

_OLD_ID = re.compile(r"^(?:arXiv:)?([a-z-]+)(?:\.[A-Z]{2})?/(\d{4})(\d{3})")
_NEW_ID = re.compile(r"^(?:arXiv:)?(\d{4})")


def is_valid_category_strict(cat: str) -> bool:
    return cat in CATEGORIES and cat not in _LEGACY


def archive_of(cat: str) -> str:
    return cat.split(".", 1)[0]


class Categories:
    def __init__(self, line: str = "", primary: str = ""):
        parts = line.split()
        self.primary = parts[0] if parts else primary
        self.secondaries: set[str] = set(parts[1:])

    def add_secondary(self, cat: str) -> int:
        if cat == self.primary or cat in self.secondaries:
            return 0
        self.secondaries.add(cat)
        return 1

    def delete_secondary(self, cat: str) -> int:
        if cat not in self.secondaries:
            return 0
        self.secondaries.discard(cat)
        return 1

    def __str__(self) -> str:
        return " ".join([self.primary, *sorted(self.secondaries)])

    def canonicalize(self) -> int:
        """Make alias pairs complete and the primary canonical. Returns the
        number of changes, 0 means it already was canonical."""
        n = 0
        if self.primary in EQUIV:
            self.primary = EQUIV[self.primary]
            n += 1
            n += self.delete_secondary(self.primary)
        primary_equiv = INV_EQUIV.get(self.primary, "")
        if primary_equiv:
            n += self.add_secondary(primary_equiv)
        for cat in sorted(self.secondaries):
            if cat == primary_equiv:
                continue
            if cat == self.primary:
                n += self.delete_secondary(cat)
            if cat in EQUIV:
                n += self.add_secondary(EQUIV[cat])
            elif cat in INV_EQUIV:
                n += self.add_secondary(INV_EQUIV[cat])
        return n

    def is_valid_for_id(self, paper_id: str) -> bool:
        """Strict validity, allowing the historical exceptions only for the
        ids they apply to."""
        id_archive = ""
        id_yyyymm = 999999
        id_yymmnnn = ""
        if m := _OLD_ID.match(paper_id):
            id_archive, yymm, nnn = m.groups()
            id_yyyymm = int(("19" if int(yymm) > 9000 else "20") + yymm)
            id_yymmnnn = yymm + nnn
            paper_id = f"{id_archive}/{yymm}{nnn}"
        elif m := _NEW_ID.match(paper_id):
            id_yyyymm = int("20" + m.group(1))

        p = self.primary
        if not (is_valid_category_strict(p) or id_yyyymm <= LEGACY_ARCHIVE_AS_PRIMARY.get(p, 0)):
            return False
        if id_archive and archive_of(p) != id_archive and paper_id not in KNOWN_BAD_PRIMARY:
            return False
        # a subsumed archive's primary needs the subsuming category as a secondary
        funct_an_to_oa = id_archive == "funct-an" and id_yymmnnn in FUNCT_AN_TO_OA
        subsumed_into = "math.OA" if funct_an_to_oa else ARCHIVES_SUBSUMED.get(id_archive)
        if subsumed_into and subsumed_into not in self.secondaries:
            return False

        for sec in self.secondaries:
            if not (is_valid_category_strict(sec) or id_yyyymm <= LEGACY_ARCHIVE_AS_SECONDARY.get(sec, 0)):
                return False
        if p in self.secondaries:  # duplicate of primary
            return False

        if p in EQUIV:  # alias not allowed as primary
            return False
        listed = {p, *self.secondaries}
        for cat in listed:
            other = EQUIV.get(cat) or INV_EQUIV.get(cat)
            if other and other not in listed:
                return False
        return True


_ABS_SPLIT = re.compile(r"^\\\\\n", re.MULTILINE)


def abs_field(raw: str, name: str) -> str | None:
    """A header field of an .abs file, continuation lines joined."""
    parts = _ABS_SPLIT.split(raw)
    header = parts[1] if len(parts) > 1 else raw
    m = re.search(rf"^{re.escape(name)}:[ \t]*(.*(?:\n[ \t]+.*)*)", header, re.MULTILINE)
    return " ".join(m.group(1).split()) if m else None
