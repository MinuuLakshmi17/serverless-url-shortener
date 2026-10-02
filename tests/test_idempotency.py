import json

import pytest

from src.handler import lambda_handler, url_repository, idempotency_repository
from src.repositories.idempotency import MemoryIdempotencyRepository
from src.repositories.memory import MemoryAnalyticsRepository, MemoryURLRepository
from src.services import URLService


@pytest.fixture(autouse=True)
def reset():
    url_repository._urls.clear()
    idempotency_repository._store.clear()
    yield


def make_service(ttl_seconds=86400):
    return URLService(
        MemoryURLRepository(),
        MemoryAnalyticsRepository(),
        MemoryIdempotencyRepository(ttl_seconds=ttl_seconds),
    )


def test_same_key_returns_same_code():
    s = make_service()
    first = s.shorten("https://example.com/a", idempotency_key="key-1")
    second = s.shorten("https://example.com/a", idempotency_key="key-1")
    assert first.short_code == second.short_code
    assert s.urls.count() == 1


def test_different_keys_mint_different_codes():
    s = make_service()
    first = s.shorten("https://example.com/a", idempotency_key="key-1")
    second = s.shorten("https://example.com/a", idempotency_key="key-2")
    assert first.short_code != second.short_code
    assert s.urls.count() == 2


def test_no_key_behaves_as_before():
    s = make_service()
    first = s.shorten("https://example.com/a")
    second = s.shorten("https://example.com/a")
    assert first.short_code != second.short_code


def test_expired_key_mints_new_code():
    s = make_service(ttl_seconds=0)  # keys expire immediately
    first = s.shorten("https://example.com/a", idempotency_key="key-1")
    second = s.shorten("https://example.com/a", idempotency_key="key-1")
    assert first.short_code != second.short_code


def test_race_loser_returns_winner_record():
    s = make_service()

    class RacyRepo(MemoryIdempotencyRepository):
        def save(self, key, short_code):
            # Simulate losing a concurrent race: someone else stored first.
            super().save("other-winner", "WINCODE1")
            raise KeyError(key)

        def get(self, key):
            if key == "race-key":
                return "WINCODE1"
            return super().get(key)

    s.idempotency = RacyRepo()
    s.urls.create("WINCODE1", "https://example.com/winner")
    record = s.shorten("https://example.com/loser", idempotency_key="race-key")
    assert record.short_code == "WINCODE1"


def _post(url, headers=None):
    event = {
        "httpMethod": "POST",
        "path": "/shorten",
        "body": json.dumps({"url": url}),
    }
    if headers:
        event["headers"] = headers
    return lambda_handler(event, None)


def test_handler_idempotency_key_header():
    first = _post("https://example.com/a", {"Idempotency-Key": "hdr-1"})
    second = _post("https://example.com/a", {"Idempotency-Key": "hdr-1"})
    assert first["statusCode"] == 201
    assert second["statusCode"] == 201
    assert json.loads(first["body"])["short_code"] == json.loads(second["body"])["short_code"]
    assert url_repository.count() == 1


def test_handler_idempotency_header_case_insensitive():
    first = _post("https://example.com/a", {"idempotency-key": "hdr-2"})
    second = _post("https://example.com/a", {"IDEMPOTENCY-KEY": "hdr-2"})
    assert json.loads(first["body"])["short_code"] == json.loads(second["body"])["short_code"]
    assert url_repository.count() == 1
