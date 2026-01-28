from pydantic import BaseModel
from typing import Optional

class NGSessionPayload(BaseModel):
    """NG session ID payload"""
    user_id: str
    session_id: str
    nonce: Optional[str] = None
    expires: str                  # ISO date format
    claims: Optional[str] = None  # NG_COOKIE_HITCHHIKER_NAME
    model_config = {
        "from_attributes": True,
        "extra": "ignore",
    }
