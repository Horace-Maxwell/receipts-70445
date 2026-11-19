"""Build a packet: every item for one company-week, plus quant inputs."""
import json
from datetime import date, timedelta

from .collect import edgar, macro, news, prices


def week_window(monday):
    """Brief date (a Monday) -> the previous Monday..Friday window."""
    m = date.fromisoformat(monday)
    start = m - timedelta(days=7)
    return start.isoformat(), (start + timedelta(days=4)).isoformat()


def collect(ticker, start, end, live_news=False):
    items = []
    items += edgar.filings(ticker, start, end)
    items += news.yahoo_latest(ticker) if live_news else news.gdelt(ticker, start, end)
    items.append(macro.fred_snapshot(end))
    items += macro.federal_register(ticker, start, end)
    return items


def number(items, prefix):
    for i, it in enumerate(items, 1):
        it["id"] = f"{prefix}-{i:02d}"
    return items


def save(path, ticker, start, end, items, feats):
    path.mkdir(parents=True, exist_ok=True)
    with open(path / "items.jsonl", "w") as f:
        for it in items:
            f.write(json.dumps(it, ensure_ascii=False) + "\n")
    meta = {"ticker": ticker, "window_start": start, "window_end": end, "features": feats}
    (path / "packet.json").write_text(json.dumps(meta, indent=2))


def load(path):
    items = [json.loads(l) for l in open(path / "items.jsonl") if l.strip()]
    meta = json.loads((path / "packet.json").read_text())
    return meta, items
