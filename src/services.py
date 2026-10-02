from datetime import datetime, timezone
from urllib.parse import urlparse
import secrets
import string
from src.config import SHORT_CODE_LENGTH, MAX_GENERATION_ATTEMPTS

class URLService:
    def __init__(self, url_repository, analytics_repository, idempotency_repository=None):
        self.urls = url_repository
        self.analytics = analytics_repository
        self.idempotency = idempotency_repository

    @staticmethod
    def validate_url(url):
        if not isinstance(url, str):
            return False
        parsed = urlparse(url.strip())
        return parsed.scheme in ("http", "https") and bool(parsed.netloc)

    @staticmethod
    def generate_short_code(length=SHORT_CODE_LENGTH):
        chars = string.ascii_letters + string.digits
        return "".join(secrets.choice(chars) for _ in range(length))

    @staticmethod
    def _normalize_expires_at(expires_at):
        """Validate an ISO-8601 expiry; return it normalized to UTC ISO format."""
        if expires_at is None:
            return None
        if not isinstance(expires_at, str):
            raise ValueError("expires_at must be an ISO-8601 datetime string")
        try:
            parsed = datetime.fromisoformat(expires_at)
        except ValueError:
            raise ValueError("expires_at must be an ISO-8601 datetime string")
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=timezone.utc)
        if parsed <= datetime.now(timezone.utc):
            raise ValueError("expires_at must be in the future")
        return parsed.isoformat()

    @staticmethod
    def _is_expired(record):
        if not record.expires_at:
            return False
        try:
            expiry = datetime.fromisoformat(record.expires_at)
        except (ValueError, TypeError):
            return False
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return datetime.now(timezone.utc) >= expiry

    def _record_for_idempotency_key(self, idempotency_key):
        short_code = self.idempotency.get(idempotency_key)
        if not short_code:
            return None
        return self.urls.get(short_code)

    def shorten(self, url, owner_id=None, expires_at=None, idempotency_key=None):
        if not self.validate_url(url):
            raise ValueError("URL must be a valid HTTP or HTTPS URL")
        expires_at = self._normalize_expires_at(expires_at)

        if idempotency_key and self.idempotency is not None:
            existing = self._record_for_idempotency_key(idempotency_key)
            if existing is not None:
                return existing

        for _ in range(MAX_GENERATION_ATTEMPTS):
            code = self.generate_short_code()
            if self.urls.exists(code):
                continue
            try:
                record = self.urls.create(code, url.strip(), owner_id, expires_at)
            except ValueError:
                continue
            if idempotency_key and self.idempotency is not None:
                try:
                    self.idempotency.save(idempotency_key, record.short_code)
                except KeyError:
                    # Lost a concurrent race: another request with the same
                    # key won; return the winner's record instead.
                    winner = self._record_for_idempotency_key(idempotency_key)
                    if winner is not None:
                        return winner
            return record
        raise RuntimeError("Unable to generate a unique short code")

    def redirect(self, short_code, headers=None):
        record = self.urls.get(short_code)
        if record is None or self._is_expired(record):
            return None
        headers = headers or {}
        self.analytics.record_click(
            short_code,
            headers.get("User-Agent"),
            headers.get("Referer"),
        )
        return record
