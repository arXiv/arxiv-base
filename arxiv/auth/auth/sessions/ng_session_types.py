from pydantic import BaseModel
from typing import Optional

# RFC 7519
class RFC7519RegisteredJwtClaims(BaseModel):
    exp: Optional[int] = None
    nbf: Optional[int] = None
    iss: Optional[str] = None
    aud: Optional[str] = None
    iat: Optional[int] = None
    sub: Optional[str] = None
    jti: Optional[str] = None

    model_config = {
        "from_attributes": True,
        "extra": "ignore",
    }

class NGSessionPayload(RFC7519RegisteredJwtClaims):
    """NG session ID payload"""
    user_id: str
    session_id: str
    nonce: str
    expires: str                  # ISO date format
    claims: Optional[str] = None  # NG_COOKIE_HITCHHIKER_NAME
    model_config = {
        "from_attributes": True,
        "extra": "ignore",
    }
