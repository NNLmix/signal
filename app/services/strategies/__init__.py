from .scalp_ema import Strategy as ScalpEMA
from .trend_pullback import Strategy as TrendPullback

STRATEGIES = [ScalpEMA(), TrendPullback()]
