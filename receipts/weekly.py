"""Weekly job: build packets and briefs for the whole watchlist.

python -m receipts.weekly --monday 2026-11-16
With the relay backend, run once to write requests, then again after they are answered.
"""
import argparse
import json

from . import agent, llm
from .collect import prices
from .config import BRIEFS_DIR, WATCHLIST
from .packet import collect, load, number, save, week_window


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--monday", required=True)
    ap.add_argument("--backend", default=None)
    ap.add_argument("--tickers", nargs="*", default=WATCHLIST)
    a = ap.parse_args()
    start, end = week_window(a.monday)
    wk = BRIEFS_DIR / a.monday
    pending = []
    for t in a.tickers:
        pdir = wk / "packets" / t
        if not (pdir / "items.jsonl").exists():
            items = number(collect(t, start, end), t)
            save(pdir, t, start, end, items, prices.features(t, end))
            print(t, len(items), "items")
        meta, items = load(pdir)
        try:
            brief = agent.run(meta, items, f"weekly__{a.monday}__{t}", a.backend)
        except llm.Pending as p:
            pending.append(str(p))
            continue
        (wk / f"{t}.json").write_text(json.dumps(brief, indent=2))
    if pending:
        print(f"{len(pending)} requests waiting in relay/requests/")


if __name__ == "__main__":
    main()
