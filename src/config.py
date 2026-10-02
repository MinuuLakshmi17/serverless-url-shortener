import os

APP_NAME = os.getenv("APP_NAME", "serverless-url-shortener")
SHORT_CODE_LENGTH = int(os.getenv("SHORT_CODE_LENGTH", "7"))
MAX_GENERATION_ATTEMPTS = int(os.getenv("MAX_GENERATION_ATTEMPTS", "10"))

# Repository backends. URL metadata: "memory" | "postgres".
# Analytics events: "memory" | "dynamodb". Idempotency: "memory" | "dynamodb".
STORAGE_BACKEND = os.getenv("STORAGE_BACKEND", "memory")
ANALYTICS_BACKEND = os.getenv("ANALYTICS_BACKEND", "memory")
IDEMPOTENCY_BACKEND = os.getenv("IDEMPOTENCY_BACKEND", "memory")

DATABASE_URL = os.getenv("DATABASE_URL", "")
DYNAMODB_CLICK_TABLE = os.getenv("DYNAMODB_CLICK_TABLE", "")
DYNAMODB_IDEMPOTENCY_TABLE = os.getenv("DYNAMODB_IDEMPOTENCY_TABLE", "")
IDEMPOTENCY_TTL_SECONDS = int(os.getenv("IDEMPOTENCY_TTL_SECONDS", "86400"))
