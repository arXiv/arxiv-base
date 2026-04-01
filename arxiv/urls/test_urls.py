
from ..identifier import Identifier

from arxiv.urls import (
    pdf_canonical_url,
    html_canonical_url,
    abs_canonical_url,
)

def test_urls():
    arxiv_id = "2002.01234v3"
    id = Identifier(arxiv_id)
    assert pdf_canonical_url(id).endswith(arxiv_id)
    assert html_canonical_url(id).endswith(arxiv_id)
    assert abs_canonical_url(id).endswith(arxiv_id)
