from redis_client import get_prices, cache_features, push_price

def update_and_compute(symbol: str, price: float, volume: float):
    push_price(symbol, price, volume)
    data = get_prices(symbol)

    if not data:
        return {}

    prices, volumes = zip(*data)
    avg_price = sum(prices) / len(prices)
    total_vol = sum(volumes)
    last_price = prices[0]  # последний пушнутый = первый в списке

    vwap = sum(p * v for p, v in data) / max(total_vol, 1)
    ema = sum(prices) / len(prices)  # упрощённый EMA (можно улучшить)

    imbalance = (last_price - avg_price) / avg_price * 100

    features = {
        "last_price": last_price,
        "ema": ema,
        "vwap": vwap,
        "imbalance": imbalance,
        "vol_sum": total_vol,
        "window_len": len(prices),
    }

    cache_features(symbol, features)
    return features
