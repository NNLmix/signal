import importlib

STRATEGY_MODULES = [
    "strategies.strat_momentum",
]

def load_strategies():
    instances = []
    for mod in STRATEGY_MODULES:
        m = importlib.import_module(mod)
        instances.append(m.Strategy(config={}))
    return instances

strategies = load_strategies()
