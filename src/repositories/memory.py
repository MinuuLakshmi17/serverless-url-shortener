from datetime import datetime, timezone
from threading import Lock
from typing import Optional
from src.models import URLRecord, ClickEvent
from src.utils import generate_event_id

class MemoryURLRepository:
    def __init__(self):
        self._urls = {}
        self._lock = Lock()

    def create(self, short_code, original_url, owner_id=None, expires_at=None):
        with self._lock:
            if short_code in self._urls:
                raise ValueError("Short code already exists")
            record = URLRecord(
                short_code=short_code,
                original_url=original_url,
                owner_id=owner_id,
                created_at=datetime.now(timezone.utc).isoformat(),
                expires_at=expires_at,
            )
            self._urls[short_code] = record
            return record

    def get(self, short_code):
        with self._lock:
            return self._urls.get(short_code)

    def exists(self, short_code):
        with self._lock:
            return short_code in self._urls

    def count(self):
        with self._lock:
            return len(self._urls)

class MemoryAnalyticsRepository:
    def __init__(self):
        self._events = []
        self._lock = Lock()

    def record_click(self, short_code, user_agent=None, referrer=None, country=None, ip_hash=None):
        event = ClickEvent(
            event_id=generate_event_id(),
            short_code=short_code,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_agent=user_agent,
            referrer=referrer,
            country=country,
            ip_hash=ip_hash,
        )
        with self._lock:
            self._events.append(event)
        return event

    def get_events(self, short_code):
        with self._lock:
            return [e for e in self._events if e.short_code == short_code]

    def count(self, short_code=None):
        with self._lock:
            if short_code is None:
                return len(self._events)
            return sum(e.short_code == short_code for e in self._events)
