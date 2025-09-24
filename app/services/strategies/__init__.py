from ...config import settings
from .btc_price_threshold import Strategy as BtcPriceThreshold
from .trend_pullback import Strategy as TrendPullback
from .four_hour_reentry import Strategy as FourHourReentry

_ALL = [
    BtcPriceThreshold(),
    TrendPullback(),
    FourHourReentry(),
]

# Apply toggles from settings.STRATEGY_TOGGLES
STRATEGIES = [s for s in _ALL if settings.STRATEGY_TOGGLES.get(getattr(s, "name", ""), True)]
