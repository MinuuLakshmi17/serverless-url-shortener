# Failure Modes

| Failure | Expected behavior | Evidence |
|---|---|---|
| Invalid URL | HTTP 400 | Automated test |
| Unknown short code | HTTP 404 | Automated test |
| Short-code collision | Retry generation | Automated test |
| Lambda timeout | No partial logical write | AWS test |
| Aurora unavailable | Controlled error + log | AWS test |
| DynamoDB throttling | Controlled retry/error strategy | AWS test |
| Duplicate idempotency key | One logical operation | AWS test |
| Expired URL | Reject redirect | AWS test |

Only claim behavior after it has actually been tested.
