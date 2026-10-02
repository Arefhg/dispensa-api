"""Structured JSON logging, with a per-request ID attached to every line.

Every log line is one JSON object: time, level, message, logger, request_id,
plus whatever extra fields the call site passed in (e.g. the access log's
method/path/status_code/duration_ms). Never log secrets here or at any call
site: no passwords, tokens, Authorization headers, or request bodies.
"""

import contextvars
import json
import logging
import sys
from datetime import UTC, datetime
from typing import Any

request_id_var: contextvars.ContextVar[str | None] = contextvars.ContextVar(
    "request_id", default=None
)

_HANDLER_NAME = "dispensa_json_handler"

# Standard attributes every LogRecord has. Anything else on a record is a
# caller-supplied extra field (e.g. method, path, status_code) and gets
# included in the JSON output automatically.
_RESERVED_ATTRS = {
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
    "taskName",
}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "time": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
            "logger": record.name,
            "request_id": getattr(record, "request_id", request_id_var.get()),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED_ATTRS and key not in payload:
                payload[key] = value
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str)


def configure_logging() -> None:
    root = logging.getLogger()

    for existing in list(root.handlers):
        if existing.get_name() == _HANDLER_NAME:
            root.removeHandler(existing)

    handler = logging.StreamHandler(sys.stdout)
    handler.set_name(_HANDLER_NAME)
    handler.setFormatter(JsonFormatter())
    root.addHandler(handler)
    root.setLevel(logging.INFO)

    # Let uvicorn's own loggers flow through our JSON handler instead of
    # uvicorn's default plain-text one.
    for name in ("uvicorn", "uvicorn.error"):
        uv_logger = logging.getLogger(name)
        uv_logger.handlers = []
        uv_logger.propagate = True

    # Our own middleware logs one structured access line per request already;
    # uvicorn's built-in access log is plain text and would duplicate it.
    access_logger = logging.getLogger("uvicorn.access")
    access_logger.handlers = []
    access_logger.disabled = True
