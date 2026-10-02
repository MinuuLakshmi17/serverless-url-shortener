from typing import Optional
import psycopg
from src.models import URLRecord

class PostgresURLRepository:
    def __init__(self, database_url: str):
        self.database_url = database_url

    def create(self, short_code, original_url, owner_id=None, expires_at=None):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    '''INSERT INTO urls
                       (id, short_code, long_url, owner_id, created_at, expires_at)
                       VALUES (gen_random_uuid(), %s, %s, %s, CURRENT_TIMESTAMP, %s)
                       RETURNING short_code, long_url, created_at, owner_id, expires_at''',
                    (short_code, original_url, owner_id, expires_at),
                )
                row = cur.fetchone()
            conn.commit()
        return URLRecord(
            short_code=row[0],
            original_url=row[1],
            created_at=row[2].isoformat(),
            owner_id=row[3],
            expires_at=row[4].isoformat() if row[4] else None,
        )

    def get(self, short_code):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    "SELECT short_code, long_url, created_at, owner_id, expires_at FROM urls WHERE short_code=%s",
                    (short_code,),
                )
                row = cur.fetchone()
        if row is None:
            return None
        return URLRecord(
            short_code=row[0],
            original_url=row[1],
            created_at=row[2].isoformat(),
            owner_id=row[3],
            expires_at=row[4].isoformat() if row[4] else None,
        )

    def exists(self, short_code):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1 FROM urls WHERE short_code=%s LIMIT 1", (short_code,))
                return cur.fetchone() is not None

    def count(self):
        with psycopg.connect(self.database_url) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM urls")
                return cur.fetchone()[0]
