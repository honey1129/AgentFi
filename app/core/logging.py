from __future__ import annotations

import json
import logging
import sys
from datetime import datetime
from decimal import Decimal


_configured = False


def configure_logging() -> None:
    global _configured
    if _configured:
        return

    logging.basicConfig(level=logging.INFO, format="%(message)s", stream=sys.stdout)
    _configured = True


def get_logger(name: str) -> logging.Logger:
    configure_logging()
    return logging.getLogger(name)


def log_event(logger: logging.Logger, event: str, **fields) -> None:
    payload = {"event": event, **fields}

    def _default(value):
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Decimal):
            return str(value)
        return str(value)

    logger.info(json.dumps(payload, default=_default, ensure_ascii=False))
