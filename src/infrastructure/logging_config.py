"""Structured JSON logging with trace_id propagation via ContextVar."""
import json
import logging
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Optional

# Set once per request by the HTTP middleware; consumed by JsonFormatter
trace_id_var: ContextVar[Optional[str]] = ContextVar("trace_id", default=None)

_EXCLUDED_LOG_RECORD_ATTRS = frozenset({
    "args", "asctime", "created", "exc_info", "exc_text", "filename",
    "funcName", "levelname", "levelno", "lineno", "message", "module",
    "msecs", "msg", "name", "pathname", "process", "processName",
    "relativeCreated", "stack_info", "thread", "threadName", "taskName",
})


class JsonFormatter(logging.Formatter):
    """Emits log records as single-line JSON with required structured fields."""

    def __init__(self, service_name: str) -> None:
        super().__init__()
        self._service = service_name

    def format(self, record: logging.LogRecord) -> str:
        entry: dict = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "service": self._service,
            "trace_id": trace_id_var.get() or "no-trace",
            "message": record.getMessage(),
            "logger": record.name,
        }

        # Include extra fields passed via logger.info(..., extra={...})
        for key, value in record.__dict__.items():
            if key not in _EXCLUDED_LOG_RECORD_ATTRS and not key.startswith("_"):
                entry[key] = value

        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str)


def setup_logging(service_name: str, level: int = logging.INFO) -> None:
    """Configure root logger with structured JSON output to stdout."""
    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter(service_name))

    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level)
    root.addHandler(handler)

    # Suppress noisy third-party loggers
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("botocore").setLevel(logging.WARNING)
    logging.getLogger("boto3").setLevel(logging.WARNING)
