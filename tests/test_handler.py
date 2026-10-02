import json
import pytest
from src.handler import lambda_handler, url_repository, analytics_repository

@pytest.fixture(autouse=True)
def reset():
    url_repository._urls.clear()
    analytics_repository._events.clear()

def test_health():
    r = lambda_handler({"httpMethod": "GET", "path": "/health"}, None)
    assert r["statusCode"] == 200
    assert json.loads(r["body"])["status"] == "healthy"

def test_create():
    r = lambda_handler({"httpMethod": "POST", "path": "/shorten",
                        "body": json.dumps({"url": "https://example.com/path"})}, None)
    assert r["statusCode"] == 201
    b = json.loads(r["body"])
    assert len(b["short_code"]) == 7
    assert b["original_url"] == "https://example.com/path"

@pytest.mark.parametrize("url", ["", "not-a-url", "ftp://example.com", "example.com"])
def test_invalid_url(url):
    r = lambda_handler({"httpMethod": "POST", "path": "/shorten",
                        "body": json.dumps({"url": url})}, None)
    assert r["statusCode"] == 400

def test_invalid_json():
    r = lambda_handler({"httpMethod": "POST", "path": "/shorten", "body": "{bad"}, None)
    assert r["statusCode"] == 400

def test_redirect_records_click():
    created = lambda_handler({"httpMethod": "POST", "path": "/shorten",
                              "body": json.dumps({"url": "https://www.binghamton.edu"})}, None)
    code = json.loads(created["body"])["short_code"]
    r = lambda_handler({"httpMethod": "GET", "path": f"/{code}",
                        "pathParameters": {"short_code": code},
                        "headers": {"User-Agent": "pytest"}}, None)
    assert r["statusCode"] == 302
    assert r["headers"]["Location"] == "https://www.binghamton.edu"
    assert analytics_repository.count(code) == 1

def test_unknown_code():
    r = lambda_handler({"httpMethod": "GET", "path": "/missing123",
                        "pathParameters": {"short_code": "missing123"}}, None)
    assert r["statusCode"] == 404

def test_analytics():
    created = lambda_handler({"httpMethod": "POST", "path": "/shorten",
                              "body": json.dumps({"url": "https://example.com"})}, None)
    code = json.loads(created["body"])["short_code"]
    lambda_handler({"httpMethod": "GET", "path": f"/{code}",
                    "pathParameters": {"short_code": code}}, None)
    r = lambda_handler({"httpMethod": "GET", "path": f"/analytics/{code}"}, None)
    assert r["statusCode"] == 200
    assert json.loads(r["body"])["clicks"] == 1
