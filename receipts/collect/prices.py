"""Daily prices from Yahoo Finance's chart endpoint (no key) and simple quant inputs."""
from datetime import date, datetime, timedelta, timezone

from ..http import get


def daily_closes(ticker, start, end):
    """Adjusted closes as [(YYYY-MM-DD, close)], start..end inclusive."""
    p1 = int(datetime.fromisoformat(start).replace(tzinfo=timezone.utc).timestamp())
    p2 = int((datetime.fromisoformat(end) + timedelta(days=1)).replace(tzinfo=timezone.utc).timestamp())
    data = get(f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker}",
               params={"period1": p1, "period2": p2, "interval": "1d", "events": "div,splits"}, as_json=True)
    res = data["chart"]["result"][0]
    ts = res.get("timestamp", [])
    adj = res["indicators"].get("adjclose", [{}])[0].get("adjclose") or res["indicators"]["quote"][0]["close"]
    out = []
    for t, c in zip(ts, adj):
        if c is not None:
            out.append((datetime.fromtimestamp(t, tz=timezone.utc).strftime("%Y-%m-%d"), float(c)))
    return out


def _ret(series, back):
    if len(series) <= back:
        return None
    return series[-1][1] / series[-1 - back][1] - 1


def features(ticker, as_of):
    """Quant inputs computed only from prices up to and including as_of."""
    start = (date.fromisoformat(as_of) - timedelta(days=400)).isoformat()
    px = [p for p in daily_closes(ticker, start, as_of) if p[0] <= as_of]
    spy = [p for p in daily_closes("SPY", start, as_of) if p[0] <= as_of]
    if len(px) < 30:
        return {}
    rets = [px[i][1] / px[i - 1][1] - 1 for i in range(len(px) - 20, len(px))]
    mean = sum(rets) / len(rets)
    vol = (sum((r - mean) ** 2 for r in rets) / (len(rets) - 1)) ** 0.5 * (252 ** 0.5)
    mom = None
    if len(px) > 252:
        mom = px[-22][1] / px[-253][1] - 1
    f = {
        "as_of": px[-1][0],
        "last_close": round(px[-1][1], 2),
        "return_5d_pct": round(100 * _ret(px, 5), 2),
        "excess_return_5d_vs_spy_pct": round(100 * (_ret(px, 5) - _ret(spy, 5)), 2),
        "return_21d_pct": round(100 * _ret(px, 21), 2),
        "momentum_12_1_pct": round(100 * mom, 2) if mom is not None else None,
        "volatility_20d_annualized_pct": round(100 * vol, 1),
    }
    return f


def excess_return(ticker, start_after, days=20):
    """Stock minus SPY total return over `days` trading days, from the first close after start_after."""
    end = (date.fromisoformat(start_after) + timedelta(days=45)).isoformat()
    px = [p for p in daily_closes(ticker, start_after, end) if p[0] > start_after]
    spy = [p for p in daily_closes("SPY", start_after, end) if p[0] > start_after]
    if len(px) <= days or len(spy) <= days:
        return None
    return (px[days][1] / px[0][1] - 1) - (spy[days][1] / spy[0][1] - 1)
