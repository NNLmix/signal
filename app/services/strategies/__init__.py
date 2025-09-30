
from ...config import settings
from .loader import load_all

# Автопоиск стратегий в пакете (каждый *.py с классом Strategy/переменной STRATEGY)
_loaded = load_all()

# Применяем флаги из settings.STRATEGY_TOGGLES
def _enabled(name: str) -> bool:
    toggles = getattr(settings, "STRATEGY_TOGGLES", {})
    return toggles.get(name, True)

STRATEGIES = [s for (name, s) in _loaded.items() if _enabled(name)]
