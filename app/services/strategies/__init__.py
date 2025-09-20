from .btc_price_threshold import Strategy as BtcPriceThreshold
from .scalp_ema import Strategy as ScalpEMA
from .trend_pullback import Strategy as TrendPullback

STRATEGIES = [BtcPriceThreshold(), ScalpEMA(), TrendPullback()]
