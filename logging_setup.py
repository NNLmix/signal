import json, logging, os, sys

def setup_json_logging(level: str = "INFO"):
    class JsonFormatter(logging.Formatter):
        def format(self, record):
            payload = {"level": record.levelname, "msg": record.getMessage(), "logger": record.name}
            if record.exc_info:
                payload["exc_info"] = self.formatException(record.exc_info)
            return json.dumps(payload, ensure_ascii=False)
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level or os.getenv("LOG_LEVEL", "INFO"))
