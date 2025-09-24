import logging
import sys
import json
from typing import Any, Mapping

class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        base = {
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key not in ("args", "msg", "exc_info", "exc_text", "stack_info"):
                try:
                    json.dumps({key: value})
                    base[key] = value
                except Exception:
                    base[key] = str(value)
        return json.dumps(base, ensure_ascii=False)

def setup_logging(level: str = "INFO"):
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.setLevel(level.upper())
    root.handlers = [handler]


# Fallback: initialize logging on import if nothing configured (safe for local tests)
try:
    if not logging.getLogger().handlers:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(JsonFormatter())
        logging.getLogger().addHandler(handler)
        logging.getLogger().setLevel(logging.INFO)
except Exception:
    pass
