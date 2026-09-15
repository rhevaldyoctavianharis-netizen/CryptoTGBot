import aiohttp
from config import COINS, BINANCE_SYMBOLS, CRYPTOPANIC_KEY, COINPAPRIKA_IDS

TIMEOUT = aiohttp.ClientTimeout(total=10)
PAPRIKA = "https://api.coinpaprika.com/v1"
NEWS_BASE = "https://cryptocurrency.cv"


async def _get(url, params=None):
    async with aiohttp.ClientSession(timeout=TIMEOUT) as s:
        async with s.get(url, params=params) as r:
            r.raise_for_status()
            return await r.json()


async def get_price(coin):
    cid = COINS[coin]
    try:
        data = await _get(
            "https://api.coingecko.com/api/v3/simple/price",
            {"ids": cid, "vs_currencies": "usd,idr",
             "include_24hr_change": "true", "include_24hr_vol": "true"})
        d = data.get(cid, {})
        return {"usd": d.get("usd"), "idr": d.get("idr"),
                "change_24h": d.get("usd_24h_change"),
                "vol_24h": d.get("usd_24h_vol")}
    except Exception:
        return await _paprika_price(coin)


async def _paprika_price(coin):
    pid = COINPAPRIKA_IDS.get(coin)
    if not pid:
        return {"usd": None, "idr": None, "change_24h": None, "vol_24h": None}
    try:
        data = await _get(f"{PAPRIKA}/tickers/{pid}")
        q = data.get("quotes", {}).get("USD", {})
        return {"usd": q.get("price"), "idr": None,
                "change_24h": q.get("percent_change_24h"),
                "vol_24h": q.get("volume_24h")}
    except Exception:
        return {"usd": None, "idr": None, "change_24h": None, "vol_24h": None}


async def get_prices_bulk(coins):
    ids = [COINS[c] for c in coins]
    try:
        data = await _get(
            "https://api.coingecko.com/api/v3/simple/price",
            {"ids": ",".join(ids), "vs_currencies": "usd",
             "include_24hr_change": "true"})
        res = {}
        id_to = {COINS[c]: c for c in coins}
        for cid, v in data.items():
            c = id_to.get(cid)
            if c:
                res[c] = {"usd": v.get("usd"),
                          "usd_24h_change": v.get("usd_24h_change")}
        return res
    except Exception:
        return await _paprika_bulk(coins)


async def _paprika_bulk(coins):
    res = {}
    for c in coins:
        pid = COINPAPRIKA_IDS.get(c)
        if not pid:
            continue
        try:
            data = await _get(f"{PAPRIKA}/tickers/{pid}")
            q = data.get("quotes", {}).get("USD", {})
            res[c] = {"usd": q.get("price"),
                      "usd_24h_change": q.get("percent_change_24h")}
        except Exception:
            continue
    return res


async def get_klines(coin, interval="4h", limit=100):
    data = await _get("https://api.binance.com/api/v3/klines",
                      {"symbol": BINANCE_SYMBOLS[coin],
                       "interval": interval, "limit": limit})
    return [float(k[4]) for k in data]


def compute_rsi(prices, period=14):
    if not prices or len(prices) < period + 1:
        return None
    gains, losses = [], []
    for i in range(1, len(prices)):
        diff = prices[i] - prices[i - 1]
        if diff >= 0:
            gains.append(diff); losses.append(0)
        else:
            gains.append(0); losses.append(-diff)
    ag = sum(gains[:period]) / period
    al = sum(losses[:period]) / period
    for i in range(period, len(gains)):
        ag = (ag * (period - 1) + gains[i]) / period
        al = (al * (period - 1) + losses[i]) / period
    if al == 0:
        return 100.0
    return 100 - (100 / (1 + ag / al))


def compute_ma(prices, period):
    if not prices or len(prices) < period:
        return None
    return sum(prices[-period:]) / period


async def get_rsi(coin, interval="4h", period=14):
    prices = await get_klines(coin, interval=interval, limit=200)
    return compute_rsi(prices, period=period)


async def get_ma_cross(coin, interval="4h"):
    prices = await get_klines(coin, interval=interval, limit=200)
    return {"ma20": compute_ma(prices, 20),
            "ma50": compute_ma(prices, 50),
            "ma200": compute_ma(prices, 200)}


async def get_fear_greed():
    data = await _get("https://api.alternative.me/fng/", {"limit": 1})
    item = data.get("data", [{}])[0]
    return {"value": int(item.get("value", 0)),
            "label": item.get("value_classification", "Unknown")}


async def get_funding(coin):
    data = await _get("https://fapi.binance.com/fapi/v1/premiumIndex",
                      {"symbol": BINANCE_SYMBOLS[coin]})
    return {"funding": float(data.get("lastFundingRate", 0)) * 100,
            "mark": float(data.get("markPrice", 0))}


async def get_news(coin, limit=5):
    endpoint = {"BTC": "bitcoin", "ETH": "ethereum", "SOL": "defi"}.get(coin, "news")
    try:
        data = await _get(f"{NEWS_BASE}/api/{endpoint}", {"limit": limit})
        return [{"title": a.get("title", ""), "url": a.get("link", ""),
                 "src": a.get("source", "")} for a in data.get("articles", [])]
    except Exception:
        pass
    if CRYPTOPANIC_KEY:
        try:
            data = await _get("https://cryptopanic.com/api/v1/posts/",
                              {"auth_token": CRYPTOPANIC_KEY,
                               "currencies": coin, "public": "true"})
            return [{"title": r.get("title", ""), "url": r.get("url", ""),
                     "src": (r.get("source") or {}).get("title", "")}
                    for r in data.get("results", [])[:limit]]
        except Exception:
            pass
    return []