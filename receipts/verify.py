"""Source check: every quote must appear verbatim in its cited item; every number must be backed."""
import json
import re

_TRANS = str.maketrans({"’": "'", "‘": "'", "“": '"', "”": '"', "–": "-", "—": "-",
                        " ": " ", " ": " ", " ": " "})


def norm(s):
    return re.sub(r"\s+", " ", (s or "").translate(_TRANS)).strip().lower()


NUM = re.compile(r"\d[\d,]*(?:\.\d+)?")


# Terms the prompt itself defines; their digits are names, not facts to source.
DEFINED_TERMS = re.compile(r"S&P\s*500|\b20[- ](?:trading[- ])?days?\b|\b20-day\b|\b2 percentage points?\b|"
                           r"\b12-1\b|\b10-[QK]\b|\b8-K\b|Form [34]\b|\b10b5-1\b|Item \d\.\d\d", re.I)


def numbers(s):
    out = set()
    s = DEFINED_TERMS.sub(" ", s or "")
    for n in NUM.findall(s):
        n = n.replace(",", "").rstrip(".")
        if "." in n:
            n = n.rstrip("0").rstrip(".")
        out.add(n)
    return out


def _backed(nums, *texts):
    pool = set()
    for t in texts:
        pool |= numbers(t)
    return {n for n in nums if n not in pool}


def check(brief, items, features):
    """Return a list of problems (empty list = pass)."""
    by_id = {it["id"]: it for it in items}
    feat_text = json.dumps(features)
    problems = []

    def quote_ok(where, item_id, quote):
        if item_id not in by_id:
            problems.append(f"{where}: cites unknown item id {item_id!r}")
            return False
        q = norm(quote)
        if len(q) < 8:
            problems.append(f"{where}: quote is too short or missing")
            return False
        if "..." in q or "…" in (quote or ""):
            problems.append(f"{where}: quote contains an ellipsis")
            return False
        src = norm(by_id[item_id]["title"] + " " + by_id[item_id]["text"])
        if q not in src:
            problems.append(f"{where}: quote not found verbatim in {item_id}: {quote[:120]!r}")
            return False
        return True

    for i, f in enumerate(brief.get("flags", [])):
        quote_ok(f"flags[{i}]", f.get("item_id"), f.get("quote"))
        missing = _backed(numbers(f.get("why")), f.get("quote"), feat_text)
        if missing:
            problems.append(f"flags[{i}].why: numbers {sorted(missing)} not in the cited quote or price inputs")
    for side in ("evidence_for", "evidence_against"):
        for i, e in enumerate(brief.get(side, [])):
            quote_ok(f"{side}[{i}]", e.get("item_id"), e.get("quote"))
            missing = _backed(numbers(e.get("claim")), e.get("quote"), feat_text)
            if missing:
                problems.append(f"{side}[{i}].claim: numbers {sorted(missing)} not in the cited quote or price inputs")
    all_text = " ".join(it["title"] + " " + it["text"] for it in items)
    for field in ("summary", "would_change_call"):
        missing = _backed(numbers(brief.get(field)), all_text, feat_text)
        if missing:
            problems.append(f"{field}: numbers {sorted(missing)} not found in any document or price input")
    if brief.get("call") not in ("Bullish", "Neutral", "Bearish"):
        problems.append(f"call must be Bullish, Neutral or Bearish, got {brief.get('call')!r}")
    if brief.get("confidence") not in (50, 60, 70, 80, 90):
        problems.append(f"confidence must be 50/60/70/80/90, got {brief.get('confidence')!r}")
    return problems
