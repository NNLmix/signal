
from __future__ import annotations
import importlib, pkgutil, sys
from pathlib import Path
from typing import Dict, Any

from .base import BaseStrategy

PKG = "app.services.strategies"

def _iter_mod_names():
    import app.services.strategies as pkg
    pkg_path = Path(pkg.__file__).parent
    for m in pkgutil.iter_modules([str(pkg_path)]):
        name = m.name
        if name.startswith("_") or name in {"base", "loader", "adapter"}:
            continue
        yield f"{PKG}.{name}"

def load_all() -> Dict[str, BaseStrategy]:
    result: Dict[str, BaseStrategy] = {}
    for mod_name in _iter_mod_names():
        try:
            mod = importlib.import_module(mod_name)
            # common patterns: class Strategy; or STRATEGY instance; or factory()
            strat = getattr(mod, "STRATEGY", None)
            if strat is None and hasattr(mod, "Strategy"):
                StratCls = getattr(mod, "Strategy")
                strat = StratCls()
            if strat is None and hasattr(mod, "factory"):
                strat = mod.factory()
            if strat and hasattr(strat, "name") and hasattr(strat, "timeframe") and hasattr(strat, "run"):
                result[strat.name] = strat
        except Exception as e:
            print(f"[strategies] failed to import {mod_name}: {e}")
            continue
    return result
