from datetime import datetime, timezone
from typing import Optional
import boto3
from boto3.dynamodb.conditions import Key
from src.models import ClickEvent
from src.utils import generate_event_id

class DynamoDBAnalyticsRepository:
    def __init__(self, table_name: str, resource=None):
        self.table = (resource or boto3.resource("dynamodb")).Table(table_name)

    def record_click(self, short_code, user_agent=None, referrer=None, country=None, ip_hash=None):
        event = ClickEvent(
            event_id=generate_event_id(),
            short_code=short_code,
            timestamp=datetime.now(timezone.utc).isoformat(),
            user_agent=user_agent,
            referrer=referrer,
            country=country,
            ip_hash=ip_hash,
        )
        item = {
            "short_code": short_code,
            "event_key": f"{event.timestamp}#{event.event_id}",
            "event_id": event.event_id,
            "timestamp": event.timestamp,
        }
        for key, value in {
            "user_agent": user_agent,
            "referrer": referrer,
            "country": country,
            "ip_hash": ip_hash,
        }.items():
            if value is not None:
                item[key] = value
        self.table.put_item(Item=item)
        return event

    def get_events(self, short_code):
        result = self.table.query(KeyConditionExpression=Key("short_code").eq(short_code))
        return [
            ClickEvent(
                event_id=i["event_id"],
                short_code=i["short_code"],
                timestamp=i["timestamp"],
                user_agent=i.get("user_agent"),
                referrer=i.get("referrer"),
                country=i.get("country"),
                ip_hash=i.get("ip_hash"),
            )
            for i in result.get("Items", [])
        ]

    def count(self, short_code=None):
        if short_code:
            return len(self.get_events(short_code))
        return int(self.table.scan(Select="COUNT").get("Count", 0))
