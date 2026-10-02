import json
from src.factory import build_repositories
from src.logging_utils import log_event
from src.services import URLService

url_repository, analytics_repository, idempotency_repository = build_repositories()
service = URLService(url_repository, analytics_repository, idempotency_repository)

def response(status_code, body, headers=None):
    h = {"Content-Type": "application/json"}
    if headers:
        h.update(headers)
    return {"statusCode": status_code, "headers": h, "body": json.dumps(body, default=str)}

def parse_body(event):
    body = event.get("body")
    if body is None or body == "":
        raise ValueError("Request body is required")
    try:
        return json.loads(body)
    except json.JSONDecodeError as exc:
        raise ValueError("Request body must contain valid JSON") from exc

def get_header(event, name):
    """Case-insensitive header lookup (API Gateway preserves client casing)."""
    headers = event.get("headers") or {}
    wanted = name.lower()
    for key, value in headers.items():
        if key.lower() == wanted:
            return value
    return None

def lambda_handler(event, context):
    method = (event.get("httpMethod") or "").upper()
    path = event.get("path") or ""
    try:
        if method == "GET" and path == "/health":
            return response(200, {
                "status": "healthy",
                "service": "serverless-url-shortener",
                "stored_urls": url_repository.count(),
                "click_events": analytics_repository.count(),
            })

        if method == "POST" and path == "/shorten":
            data = parse_body(event)
            url = data.get("url")
            if not isinstance(url, str) or not url.strip():
                return response(400, {"error": "A URL is required"})
            idempotency_key = get_header(event, "Idempotency-Key")
            record = service.shorten(
                url,
                data.get("owner_id"),
                data.get("expires_at"),
                idempotency_key=idempotency_key,
            )
            log_event("url_created", short_code=record.short_code)
            return response(201, {
                "short_code": record.short_code,
                "original_url": record.original_url,
                "created_at": record.created_at,
                "expires_at": record.expires_at,
            })

        if method == "GET" and path.startswith("/analytics/"):
            code = path.split("/analytics/", 1)[1]
            events = analytics_repository.get_events(code)
            return response(200, {
                "short_code": code,
                "clicks": len(events),
                "events": [e.__dict__ for e in events],
            })

        if method == "GET":
            params = event.get("pathParameters") or {}
            code = params.get("short_code") or path.strip("/")
            if not code:
                return response(400, {"error": "Short code is required"})
            record = service.redirect(code, event.get("headers") or {})
            if record is None:
                return response(404, {"error": "Short URL not found or expired"})
            return {"statusCode": 302, "headers": {"Location": record.original_url}, "body": ""}

        return response(404, {"error": "Not Found"})
    except ValueError as exc:
        return response(400, {"error": str(exc)})
    except Exception as exc:
        log_event("unhandled_error", error=str(exc), path=path, method=method)
        return response(500, {"error": "Internal server error"})
