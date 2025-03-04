from . import Identifier

def test_id_without_extra():
    arxiv_id = Identifier('physics/0303098')
    assert (arxiv_id
            and arxiv_id.id == 'physics/0303098'
            and arxiv_id.archive == 'physics'
            and arxiv_id.year == 2003 and arxiv_id.month == 3
            and arxiv_id.num == 98)
    assert (arxiv_id.is_old_id
            and not arxiv_id.extra
            and not arxiv_id.arxiv_prefix)


def test_id_trailing_slash():
    arxiv_id = Identifier('physics/0303098/')
    assert (arxiv_id
            and arxiv_id.id == 'physics/0303098'
            and arxiv_id.archive == 'physics'
            and arxiv_id.year == 2003 and arxiv_id.month == 3
            and arxiv_id.num == 98)
    assert (arxiv_id.is_old_id
            and arxiv_id.extra == "/"
            and not arxiv_id.arxiv_prefix)

def test_id_with_extra():
    arxiv_id = Identifier('physics/0303098/static/icon.png')
    assert (arxiv_id
            and arxiv_id.id == 'physics/0303098'
            and arxiv_id.archive == 'physics'
            and arxiv_id.year == 2003 and arxiv_id.month == 3
            and arxiv_id.num == 98)
    assert (arxiv_id.is_old_id
            and arxiv_id.arxiv_prefix == False)
    assert (arxiv_id.extra == '/static/icon.png')
