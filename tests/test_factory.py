import pytest

from src.factory import build_repositories
from src.repositories.dynamodb import DynamoDBAnalyticsRepository
from src.repositories.idempotency import (
    DynamoDBIdempotencyRepository,
    MemoryIdempotencyRepository,
)
from src.repositories.memory import MemoryAnalyticsRepository, MemoryURLRepository
from src.repositories.postgres import PostgresURLRepository

BACKEND_VARS = [
    "STORAGE_BACKEND",
    "ANALYTICS_BACKEND",
    "IDEMPOTENCY_BACKEND",
    "DATABASE_URL",
    "DYNAMODB_CLICK_TABLE",
    "DYNAMODB_IDEMPOTENCY_TABLE",
]


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in BACKEND_VARS:
        monkeypatch.delenv(var, raising=False)
    yield


def test_defaults_are_memory(monkeypatch):
    urls, analytics, idempotency = build_repositories()
    assert isinstance(urls, MemoryURLRepository)
    assert isinstance(analytics, MemoryAnalyticsRepository)
    assert isinstance(idempotency, MemoryIdempotencyRepository)


def test_unknown_storage_backend_rejected(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "cassandra")
    with pytest.raises(RuntimeError, match="STORAGE_BACKEND"):
        build_repositories()


def test_unknown_analytics_backend_rejected(monkeypatch):
    monkeypatch.setenv("ANALYTICS_BACKEND", "bigquery")
    with pytest.raises(RuntimeError, match="ANALYTICS_BACKEND"):
        build_repositories()


def test_unknown_idempotency_backend_rejected(monkeypatch):
    monkeypatch.setenv("IDEMPOTENCY_BACKEND", "redis")
    with pytest.raises(RuntimeError, match="IDEMPOTENCY_BACKEND"):
        build_repositories()


def test_postgres_requires_database_url(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "postgres")
    with pytest.raises(RuntimeError, match="DATABASE_URL"):
        build_repositories()


def test_postgres_selected_with_database_url(monkeypatch):
    monkeypatch.setenv("STORAGE_BACKEND", "postgres")
    monkeypatch.setenv("DATABASE_URL", "postgresql://localhost/db")
    urls, _, _ = build_repositories()
    assert isinstance(urls, PostgresURLRepository)


def test_dynamodb_analytics_requires_table(monkeypatch):
    monkeypatch.setenv("ANALYTICS_BACKEND", "dynamodb")
    with pytest.raises(RuntimeError, match="DYNAMODB_CLICK_TABLE"):
        build_repositories()


def test_dynamodb_backends_selected(monkeypatch):
    monkeypatch.setenv("ANALYTICS_BACKEND", "dynamodb")
    monkeypatch.setenv("IDEMPOTENCY_BACKEND", "dynamodb")
    monkeypatch.setenv("DYNAMODB_CLICK_TABLE", "clicks")
    monkeypatch.setenv("DYNAMODB_IDEMPOTENCY_TABLE", "idem")

    class FakeTable:
        def __init__(self, name):
            self.name = name

    class FakeResource:
        def Table(self, name):
            return FakeTable(name)

    import boto3

    monkeypatch.setattr(boto3, "resource", lambda *a, **k: FakeResource())
    urls, analytics, idempotency = build_repositories()
    assert isinstance(urls, MemoryURLRepository)
    assert isinstance(analytics, DynamoDBAnalyticsRepository)
    assert isinstance(idempotency, DynamoDBIdempotencyRepository)
    assert analytics.table.name == "clicks"
    assert idempotency.table.name == "idem"
