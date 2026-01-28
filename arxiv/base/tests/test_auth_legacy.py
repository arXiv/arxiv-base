
from arxiv.auth.auth.sessions.ng_session_types import NGSessionPayload

def test_ng_session_payload():
    ngsp = NGSessionPayload(
        user_id="userid",
        session_id="sessionid",
        expires="expires",
    )
    assert ngsp

