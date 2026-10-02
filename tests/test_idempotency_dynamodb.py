"""Live DynamoDB tests for the idempotency repository (moto)."""

import time

import boto3
import pytest
from moto import mock_aws

from src.repositories.idempotency import DynamoDBIdempotencyRepository


@pytest.fixture()
def repo():
    with mock_aws():
        resource = boto3.resource("dynamodb", region_name="us-east-1")
        resource.create_table(
            TableName="idem",
            KeySchema=[{"AttributeName": "idempotency_key", "KeyType": "HASH"}],
            AttributeDefinitions=[
                {"AttributeName": "idempotency_key", "AttributeType": "S"}
            ],
            BillingMode="PAY_PER_REQUEST",
        )
        yield DynamoDBIdempotencyRepository("idem", resource=resource)


def test_save_and_get_roundtrip(repo):
    repo.save("k1", "ABC1234")
    assert repo.get("k1") == "ABC1234"


def test_unknown_key_returns_none(repo):
    assert repo.get("nope") is None


def test_duplicate_save_raises_key_error(repo):
    repo.save("k1", "ABC1234")
    with pytest.raises(KeyError):
        repo.save("k1", "XYZ9999")
    # Original mapping is untouched.
    assert repo.get("k1") == "ABC1234"


def test_expired_entry_returns_none(repo):
    repo._ttl_seconds = 0
    repo.save("k1", "ABC1234")
    time.sleep(1.05)
    assert repo.get("k1") is None


def test_missing_table_name_rejected():
    with pytest.raises(ValueError):
        DynamoDBIdempotencyRepository("")
