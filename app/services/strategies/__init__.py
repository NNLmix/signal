from signal.app.config import settings
from .loader import load_all

_loaded = load_all()

def _enabled(name: str) -> bool:
    toggles = getattr(settings, "STRATEGY_TOGGLES", {}) or {}
    return toggles.get(name, True)

STRATEGIES = [s for (name, s) in _loaded.items() if _enabled(name)]
