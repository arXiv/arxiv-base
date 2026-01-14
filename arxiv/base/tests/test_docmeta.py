from typing import Any, Dict
from unittest import TestCase, mock
from datetime import datetime

from arxiv.document.metadata import DocMetadata, AuthorList, Submitter
from arxiv.taxonomy.definitions import CATEGORIES
from arxiv.identifier import Identifier
from arxiv.license import License
from arxiv.document.version import VersionEntry, SourceFlag

SAMPLE_DOCMETA = DocMetadata(
    raw_safe="abs text here",
    arxiv_id="1204.5678",
    arxiv_id_v="1204.5678v1",
    arxiv_identifier=Identifier("1204.5678v1"),
    title="title of paper",
    abstract="also abs text here",
    authors=AuthorList("First Name, Second, Name"),
    submitter=Submitter(name="a submitter", email="fakeemail@arxiv.org"),
    categories="hep-th cs.NA math-ph math.MP",
    primary_category=CATEGORIES["hep-th"],
    primary_archive=CATEGORIES["hep-th"].get_archive(),
    primary_group=CATEGORIES["hep-th"].get_archive().get_group(),
    secondary_categories=[
        CATEGORIES["math-ph"],
        CATEGORIES["math.MP"],
        CATEGORIES["cs.NA"],
    ],
    journal_ref="journal of mystical knowledge",
    report_num=None,
    doi=None,
    acm_class=None,
    msc_class=None,
    proxy=None,
    comments="very insightful comments",
    version=1,
    license=License(),
    version_history=[
        VersionEntry(
            version=1,
            raw="",
            submitted_date=None,  # type: ignore
            size_kilobytes=30,  # type: ignore
            source_flag=SourceFlag("D"),  # type: ignore
        )
    ],
    modified=datetime(year=2011, month=3, day=7),
)


class DocMetadataTest(TestCase):
    fields: Dict[str, Any]

    def __init__(self, *args: str, **kwargs: Dict) -> None:
        """Set up some common variables."""
        super().__init__(*args, **kwargs)
        self.fields = {
            # TODO: reasonable mock defaults for future tests
        }

    def test_something(self):
        """Tests that omission of a required field generates an exception."""
        fields = self.fields.copy()
        # TODO: implement a test on a generated DocMetadata

    def test_required_fields(self):
        """Tests that omission of a required field generates an exception."""
        fields = self.fields.copy()

        def run_on_empty_args() -> DocMetadata:
            return DocMetadata(**fields)  # type: ignore

        with self.assertRaises(TypeError) as ctx:
            run_on_empty_args()

        # Do not indent us or we will not run and be tested!:
        self.assertTrue(
            "missing 14 required positional arguments" in str(ctx.exception)
        )
        #
        self.assertTrue("raw_safe" in str(ctx.exception))
        self.assertTrue("arxiv_id" in str(ctx.exception))
        self.assertTrue("arxiv_id_v" in str(ctx.exception))
        self.assertTrue("arxiv_identifier" in str(ctx.exception))
        self.assertTrue("modified" in str(ctx.exception))
        self.assertTrue("title" in str(ctx.exception))
        self.assertTrue("abstract" in str(ctx.exception))
        self.assertTrue("authors" in str(ctx.exception))
        self.assertTrue("submitter" in str(ctx.exception))
        self.assertTrue("categories" in str(ctx.exception))
        self.assertTrue("primary_category" in str(ctx.exception))
        self.assertTrue("primary_archive" in str(ctx.exception))
        self.assertTrue("primary_group" in str(ctx.exception))
        self.assertTrue("secondary_categories" in str(ctx.exception))
        #
        self.assertTrue("journal_ref" not in str(ctx.exception))
        self.assertTrue("report_num" not in str(ctx.exception))
        self.assertTrue("doi" not in str(ctx.exception))
        self.assertTrue("acm_class" not in str(ctx.exception))
        self.assertTrue("msc_class" not in str(ctx.exception))
        self.assertTrue("proxy" not in str(ctx.exception))
        self.assertTrue("comments" not in str(ctx.exception))
        self.assertTrue("version" not in str(ctx.exception))
        self.assertTrue("license" not in str(ctx.exception))
        self.assertTrue("version_history" not in str(ctx.exception))
        self.assertTrue("private" not in str(ctx.exception))

    def test_get_seconaries(self):
        # get secondaries should only return cannonical instance of each secondary category with no duplicates

        self.assertEqual(
            SAMPLE_DOCMETA.get_secondaries(),
            set([CATEGORIES["math-ph"], CATEGORIES["math.NA"]]),
            "only retrieves canonical version of each secondary",
        )

        self.assertEqual(
            SAMPLE_DOCMETA.display_secondaries(),
            ["Mathematical Physics (math-ph)", "Numerical Analysis (math.NA)"],
            "secondary display string must match",
        )
