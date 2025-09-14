import logging, os, sys
LOG_LEVEL = os.getenv("LOG_LEVEL","INFO").upper()
handler = logging.StreamHandler(sys.stdout)
formatter = logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s", "%Y-%m-%dT%H:%M:%SZ")
handler.setFormatter(formatter)
root = logging.getLogger()
root.setLevel(LOG_LEVEL)
if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
    root.addHandler(handler)
logger = logging.getLogger("bot")
