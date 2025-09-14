import importlib, logging, pathlib, pkgutil
from typing import List
logger = logging.getLogger(__name__)

def load_strategies() -> List[object]:
    pkg = "strategies"
    base = pathlib.Path(__file__).parent / pkg
    strategies = []
    for m in pkgutil.iter_modules([str(base)]):
        if m.name.startswith("_"): continue
        mod = importlib.import_module(f"{pkg}.{m.name}")
        if hasattr(mod, "Strategy"):
            try:
                inst = mod.Strategy({})
                if not getattr(inst, "name", None): inst.name = m.name
                strategies.append(inst)
                logger.info("strategy.loaded %s", {"name": inst.name})
            except Exception as e:
                logger.warning("strategy.load_failed %s", {"module": m.name, "error": str(e)})
    return strategies

STRATEGIES = load_strategies()
