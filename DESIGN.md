# System Design

## Goal

Use a URL-shortening workload to study production-shaped serverless engineering: data modeling, persistence choices, reliability, observability, and performance.

## Storage

**Aurora PostgreSQL:** users and authoritative URL metadata requiring relational integrity, uniqueness, and transactions.

**DynamoDB:** click events and ephemeral/idempotency data requiring key-based access and high-volume writes.

## Planned relational model

`users(id, email, created_at)`

`urls(id, short_code, long_url, owner_id, created_at, expires_at)`

`short_code` is unique and `owner_id` references `users.id`.

## Click events

DynamoDB partition key: `short_code`

Sort key: `timestamp#event_id`

Attributes include user agent, referrer, country, and hashed IP.

## Reliability questions

- Lambda timeouts
- Aurora connectivity failures
- DynamoDB throttling
- duplicate requests
- short-code collisions
- partial failures
- expiration

## Schema evolution

Liquibase migrations follow an expand -> migrate -> contract approach.

## Observability

CloudWatch will provide structured logs, metrics, errors, latency measurements, and alarms.

## Performance

Measure p50, p95, p99, throughput, and error rate under controlled load.
