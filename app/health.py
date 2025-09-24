import logging
from typing import Dict, Any

log = logging.getLogger("startup.health")

async def startup_probe() -> Dict[str, Any]:
    """Lightweight health probe used at startup if needed."""
    try:
        return {"ok": True}
    except Exception as e:
        log.exception("startup_probe_error")
        return {"ok": False, "error": str(e)}
