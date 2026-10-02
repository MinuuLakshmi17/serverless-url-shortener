"""Idempotency-key storage for POST /shorten.

Maps a client-supplied idempotency key to the short code that was created
for it, so retried requests return the original record instead of minting
a second short URL.

Contract for both backends:
  - get(key) -> short code string, or None when unknown/expired.
  - save(key, short_code) -> stores the mapping; raises KeyError if a
    live mapping for the key already exists (lost a concurrent race).
"""

import time
from threading import Lock

import boto3
from botocore.exceptions import ClientError


class MemoryIdempotencyRepository:
    def __init__(self, ttl_seconds=86400):
        self._store = {}
        self._lock = Lock()
        self._ttl_seconds = ttl_seconds

    def get(self, key):
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return None
            short_code, expires_at = entry
            if time.time() >= expires_at:
                del self._store[key]
                return None
            return short_code

    def save(self, key, short_code):
        with self._lock:
            entry = self._store.get(key)
            if entry is not None and time.time() < entry[1]:
                raise KeyError(key)
            self._store[key] = (short_code, time.time() + self._ttl_seconds)


class DynamoDBIdempotencyRepository:
    """Backed by the IdempotencyTable from template.yaml.

    Table schema: partition key ``idempotency_key`` (S), attributes
    ``short_code`` (S) and ``expires_at`` (N, unix epoch seconds, TTL).
    """

    def __init__(self, table_name, ttl_seconds=86400, resource=None):
        if not table_name:
            raise ValueError("A DynamoDB table name is required")
        self.table = (resource or boto3.resource("dynamodb")).Table(table_name)
        self._ttl_seconds = ttl_seconds

    def get(self, key):
        result = self.table.get_item(Key={"idempotency_key": key})
        item = result.get("Item")
        if not item:
            return None
        if int(time.time()) >= int(item.get("expires_at", 0)):
            return None
        return item.get("short_code")

    def save(self, key, short_code):
        expires_at = int(time.time()) + self._ttl_seconds
        try:
            self.table.put_item(
                Item={
                    "idempotency_key": key,
                    "short_code": short_code,
                    "expires_at": expires_at,
                },
                ConditionExpression="attribute_not_exists(idempotency_key)",
            )
        except ClientError as exc:
            if exc.response.get("Error", {}).get("Code") == "ConditionalCheckFailedException":
                raise KeyError(key) from exc
            raise
