from dataclasses import dataclass
from typing import Optional

@dataclass(frozen=True)
class URLRecord:
    short_code: str
    original_url: str
    created_at: str
    owner_id: Optional[str] = None
    expires_at: Optional[str] = None

@dataclass(frozen=True)
class ClickEvent:
    event_id: str
    short_code: str
    timestamp: str
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    country: Optional[str] = None
    ip_hash: Optional[str] = None
