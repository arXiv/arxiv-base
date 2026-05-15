from arxiv.metadata.checksum import checksum_metadata


def test_checksum_metadata():
    class Md1:
        def __init__(self):
            self.title = "bogus value"
            self.authors = "bogus value"
            self.abstract = "bogus value"
            self.comments = "bogus value"
            self.report_num = "bogus value"
            self.journal_ref = "bogus value"
            self.doi = "bogus value"
            self.msc_class = "bogus value"
            self.acm_class = "bogus value"

    class Md2:
        def __init__(self):
            self.title = "another value"
            self.authors = "another value"
            self.abstract = "another value"
            self.comments = "another value"
            self.report_num = "another value"
            self.journal_ref = "another value"
            self.doi = "another value"
            self.msc_class = "another value"
            self.acm_class = "another value"

    assert checksum_metadata(Md1()) == checksum_metadata(Md1())
    assert checksum_metadata(Md2()) == checksum_metadata(Md2())
    assert checksum_metadata(Md1()) != checksum_metadata(Md2())
