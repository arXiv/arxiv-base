from arxiv.metadata.checksum import checksum_metadata

def test_checksum_metadata():
    class Md1:
        def __init__(self):
                self.title="bogus value"
                self.authors="bogus value"
                self.abstract="bogus value"
                self.comments="bogus value"
                self.report_num="bogus value"
                self.journal_ref="bogus value"
                self.doi="bogus value"
                self.msc_class="bogus value"
                self.acm_class="bogus value"

    assert checksum_metadata(Md1())
