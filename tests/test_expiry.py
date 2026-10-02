import json
from datetime import datetime, timedelta, timezone

import pytest

from src.handler import lambda_handler, url_repository, analytics_repository
from src.repositories.memory import MemoryAnalyticsRepository, MemoryURLRepository
from src.services import URLService


@pytest.fixture(autouse=True)
def reset():
    url_repository._urls.clear()
    analytics_repository._events.clear()
    yield


def future_iso():
    return (datetime.now(timezone.utc) + timedelta(days=1)).isoformat()


def past_iso():
    return (datetime.now(timezone.utc) - timedelta(days=1)).isoformat()


def make_service():
    return URLService(MemoryURLRepository(), MemoryAnalyticsRepository())


def test_past_expiry_rejected():
    s = make_service()
    with pytest.raises(ValueError):
        s.shorten("https://example.com", expires_at=past_iso())


def test_malformed_expiry_rejected():
    s = make_service()
    with pytest.raises(ValueError):
        s.shorten("https://example.com", expires_at="not-a-date")


def test_future_expiry_accepted_and_normalized():
    s = make_service()
    record = s.shorten("https://example.com", expires_at=future_iso())
    assert record.expires_at is not None
    # Round-trips as a valid ISO datetime.
    datetime.fromisoformat(record.expires_at)


def test_redirect_serves_unexpired_url():
    s = make_service()
    record = s.shorten("https://example.com", expires_at=future_iso())
    assert s.redirect(record.short_code) is not None


def test_redirect_blocks_expired_url():
    s = make_service()
    # Bypass creation-time validation to simulate a URL that expired
    # after it was stored.
    record = s.urls.create("EXP1234", "https://example.com", expires_at=past_iso())
    assert s.redirect(record.short_code) is None
    # Expired hits are not recorded as clicks.
    assert s.analytics.count(record.short_code) == 0


def test_handler_rejects_past_expiry_with_400():
    r = lambda_handler(
        {
            "httpMethod": "POST",
            "path": "/shorten",
            "body": json.dumps({"url": "https://example.com", "expires_at": past_iso()}),
        },
        None,
    )
    assert r["statusCode"] == 400


def test_handler_404_for_expired_url():
    url_repository.create("OLD1234", "https://example.com", expires_at=past_iso())
    r = lambda_handler(
        {
            "httpMethod": "GET",
            "path": "/OLD1234",
            "pathParameters": {"short_code": "OLD1234"},
        },
        None,
    )
    assert r["statusCode"] == 404


def test_handler_redirects_unexpired_url():
    created = lambda_handler(
        {
            "httpMethod": "POST",
            "path": "/shorten",
            "body": json.dumps({"url": "https://example.com", "expires_at": future_iso()}),
        },
        None,
    )
    assert created["statusCode"] == 201
    code = json.loads(created["body"])["short_code"]
    r = lambda_handler(
        {"httpMethod": "GET", "path": f"/{code}", "pathParameters": {"short_code": code}},
        None,
    )
    assert r["statusCode"] == 302
