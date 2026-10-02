import json
from src.handler import lambda_handler

created = lambda_handler(
    {"httpMethod": "POST", "path": "/shorten",
     "body": json.dumps({"url": "https://example.com"})}, None)
print("CREATE:", json.dumps(created, indent=2))

code = json.loads(created["body"])["short_code"]

redirected = lambda_handler(
    {"httpMethod": "GET", "path": f"/{code}",
     "pathParameters": {"short_code": code}}, None)
print("REDIRECT:", json.dumps(redirected, indent=2))

analytics = lambda_handler(
    {"httpMethod": "GET", "path": f"/analytics/{code}"}, None)
print("ANALYTICS:", json.dumps(analytics, indent=2))
