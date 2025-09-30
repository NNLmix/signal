from __future__ import annotations
import importlib, pkgutil
from pathlib import Path
from typing import Dict
from .base import BaseStrategy

PKG = "signal.app.services.strategies"

def _iter_mods():
    import signal.app.services.strategies as pkg
    pkg_path = Path(pkg.__file__).parent
    for m in pkgutil.iter_modules([str(pkg_path)]):
        name = m.name
        if name.startswith("_") or name in {"base","loader","adapter"}:
            continue
        yield f"{PKG}.{name}"

def load_all() -> Dict[str, BaseStrategy]:
    res: Dict[str, BaseStrategy] = {}
    for mod_name in _iter_mods():
        try:
            mod = importlib.import_module(mod_name)
            strat = getattr(mod, "STRATEGY", None)
            if strat is None and hasattr(mod, "Strategy"):
                strat = getattr(mod, "Strategy")()
            if strat is None and hasattr(mod, "factory"):
                strat = mod.factory()
            if strat and hasattr(strat, "name") and hasattr(strat, "timeframe") and hasattr(strat, "run"):
                res[strat.name] = strat
        except Exception as e:
            print(f"[strategies] failed to import {mod_name}: {e}")
            continue
    return res
