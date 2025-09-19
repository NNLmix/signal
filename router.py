import importlib, logging, pathlib, pkgutil
from typing import List

logger = logging.getLogger(__name__)

def load_strategies() -> List[object]:
    base_dir = pathlib.Path(__file__).parent / "strategies"
    pkg = __package__ + ".strategies" if __package__ else "strategies"
    strategies = []
    if not base_dir.exists():
        logger.warning("strategies directory not found: %s", base_dir)
        return strategies
    for m in pkgutil.iter_modules([str(base_dir)]):
        if m.name.startswith("_"):
            continue
        module_name = f"{pkg}.{m.name}"
        try:
            mod = importlib.import_module(module_name)
        except Exception as e:
            logger.warning("strategy.import_failed %s", {"module": module_name, "error": str(e)})
            continue
        if hasattr(mod, "Strategy"):
            try:
                inst = mod.Strategy({})
                if not getattr(inst, "name", None):
                    inst.name = m.name
                strategies.append(inst)
                logger.info("strategy.loaded %s", {"name": inst.name})
            except Exception as e:
                logger.warning("strategy.load_failed %s", {"module": m.name, "error": str(e)})
    return strategies

STRATEGIES = load_strategies()
