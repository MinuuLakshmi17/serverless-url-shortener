"""Repository factory: selects backends from environment variables.

URL metadata:      STORAGE_BACKEND     "memory" | "postgres"
Click analytics:   ANALYTICS_BACKEND   "memory" | "dynamodb"
Idempotency keys:  IDEMPOTENCY_BACKEND "memory" | "dynamodb"

Reads the environment at call time (not import time) so tests can switch
backends with monkeypatched env vars.
"""

import os

from src import config
from src.repositories.dynamodb import DynamoDBAnalyticsRepository
from src.repositories.idempotency import (
    DynamoDBIdempotencyRepository,
    MemoryIdempotencyRepository,
)
from src.repositories.memory import MemoryAnalyticsRepository, MemoryURLRepository
from src.repositories.postgres import PostgresURLRepository


def _setting(name, default):
    return os.getenv(name, getattr(config, name, default))


def build_repositories():
    """Return (url_repository, analytics_repository, idempotency_repository)."""
    storage = _setting("STORAGE_BACKEND", "memory").strip().lower()
    analytics = _setting("ANALYTICS_BACKEND", "memory").strip().lower()
    idempotency = _setting("IDEMPOTENCY_BACKEND", "memory").strip().lower()

    if storage == "memory":
        url_repository = MemoryURLRepository()
    elif storage == "postgres":
        database_url = _setting("DATABASE_URL", "")
        if not database_url:
            raise RuntimeError("DATABASE_URL is required when STORAGE_BACKEND=postgres")
        url_repository = PostgresURLRepository(database_url)
    else:
        raise RuntimeError(
            "Unknown STORAGE_BACKEND %r (expected 'memory' or 'postgres')" % storage
        )

    if analytics == "memory":
        analytics_repository = MemoryAnalyticsRepository()
    elif analytics == "dynamodb":
        table = _setting("DYNAMODB_CLICK_TABLE", "")
        if not table:
            raise RuntimeError(
                "DYNAMODB_CLICK_TABLE is required when ANALYTICS_BACKEND=dynamodb"
            )
        analytics_repository = DynamoDBAnalyticsRepository(table)
    else:
        raise RuntimeError(
            "Unknown ANALYTICS_BACKEND %r (expected 'memory' or 'dynamodb')" % analytics
        )

    ttl_seconds = int(_setting("IDEMPOTENCY_TTL_SECONDS", "86400"))
    if idempotency == "memory":
        idempotency_repository = MemoryIdempotencyRepository(ttl_seconds=ttl_seconds)
    elif idempotency == "dynamodb":
        table = _setting("DYNAMODB_IDEMPOTENCY_TABLE", "")
        if not table:
            raise RuntimeError(
                "DYNAMODB_IDEMPOTENCY_TABLE is required when IDEMPOTENCY_BACKEND=dynamodb"
            )
        idempotency_repository = DynamoDBIdempotencyRepository(
            table, ttl_seconds=ttl_seconds
        )
    else:
        raise RuntimeError(
            "Unknown IDEMPOTENCY_BACKEND %r (expected 'memory' or 'dynamodb')"
            % idempotency
        )

    return url_repository, analytics_repository, idempotency_repository
