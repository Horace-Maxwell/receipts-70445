"""FRED macro snapshot (no key) and Federal Register policy items (no key)."""
import csv
import io

from ..config import COMPANIES
from ..http import get

SERIES = {"DFF": "Effective federal funds rate (%)", "DGS10": "10-year Treasury yield (%)",
          "UNRATE": "Unemployment rate (%)", "CPIAUCSL": "CPI, all items (index)"}


def _series(sid):
    text = get("https://fred.stlouisfed.org/graph/fredgraph.csv", params={"id": sid})
    rows = [r for r in csv.reader(io.StringIO(text))][1:]
    return [(d, float(v)) for d, v in rows if v not in ("", ".")]


def fred_snapshot(end):
    lines = []
    for sid, label in SERIES.items():
        obs = [o for o in _series(sid) if o[0] <= end]
        if len(obs) < 2:
            continue
        (d1, v1) = obs[-1]
        # value about one month earlier for context
        prior = [o for o in obs if o[0] <= _minus_days(d1, 30)]
        if prior:
            d0, v0 = prior[-1]
            lines.append(f"{label}: {v1:g} on {d1} (was {v0:g} on {d0}).")
        else:
            lines.append(f"{label}: {v1:g} on {d1}.")
    return {"source": "FRED (St. Louis Fed)", "kind": "macro", "date": end,
            "url": "https://fred.stlouisfed.org/", "title": "Macro snapshot", "text": " ".join(lines)}


def _minus_days(d, n):
    from datetime import date, timedelta
    return (date.fromisoformat(d) - timedelta(days=n)).isoformat()


def federal_register(ticker, start, end, max_items=2):
    term = COMPANIES[ticker]["policy"]
    params = {"per_page": max_items, "order": "relevance", "conditions[term]": term,
              "conditions[publication_date][gte]": start, "conditions[publication_date][lte]": end,
              "conditions[type][]": ["RULE", "PRORULE", "PRESDOCU"],
              "fields[]": ["title", "publication_date", "html_url", "abstract", "agencies"]}
    try:
        data = get("https://www.federalregister.gov/api/v1/documents.json", params=params, as_json=True)
    except Exception:
        return []
    items = []
    for d in data.get("results", []):
        agencies = ", ".join(a.get("name", "") for a in d.get("agencies", []) if a.get("name"))
        items.append({"source": "Federal Register", "kind": "policy", "date": d["publication_date"],
                      "url": d["html_url"], "title": d["title"],
                      "text": f"{d['title']} ({agencies}). " + (d.get("abstract") or "")})
    return items
