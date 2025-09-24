from .btc_price_threshold import Strategy as BtcPriceThreshold
from .trend_pullback import Strategy as TrendPullback

STRATEGIES = [BtcPriceThreshold(), TrendPullback()]
