import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def log_event(name: str, **fields):
    logger.info(json.dumps({"event": name, **fields}, default=str))
