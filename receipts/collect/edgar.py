"""SEC EDGAR: filings for one company in a date window, turned into items."""
import re
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

from ..http import get

MAX_CHARS = 7000
ITEM_NAMES = {
    "1.01": "Entry into a Material Definitive Agreement", "1.02": "Termination of a Material Definitive Agreement",
    "1.05": "Material Cybersecurity Incidents", "2.01": "Completion of Acquisition or Disposition of Assets",
    "2.02": "Results of Operations and Financial Condition", "2.03": "Creation of a Direct Financial Obligation",
    "2.05": "Costs Associated with Exit or Disposal Activities", "2.06": "Material Impairments",
    "3.01": "Notice of Delisting or Transfer of Listing", "3.02": "Unregistered Sales of Equity Securities",
    "3.03": "Material Modification to Rights of Security Holders", "4.01": "Change in Certifying Accountant",
    "4.02": "Non-Reliance on Previously Issued Financial Statements",
    "5.02": "Departure or Appointment of Directors or Officers", "5.03": "Amendments to Articles or Bylaws",
    "5.07": "Submission of Matters to a Vote of Security Holders", "7.01": "Regulation FD Disclosure",
    "8.01": "Other Events", "9.01": "Financial Statements and Exhibits",
}
FORM4_CODES = {"P": "open-market purchase", "S": "open-market sale", "A": "grant or award", "M": "option exercise",
               "F": "shares withheld for tax", "G": "gift", "D": "disposition to issuer", "C": "conversion"}


def _tickers():
    return get("https://www.sec.gov/files/company_tickers.json", sec=True, as_json=True)


def cik_for(ticker):
    for row in _tickers().values():
        if row["ticker"].upper() == ticker.upper():
            return int(row["cik_str"]), row["title"]
    raise KeyError(ticker)


def _clean(html):
    soup = BeautifulSoup(html, "html.parser")
    for t in soup(["script", "style"]):
        t.decompose()
    text = soup.get_text(" ")
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _strip_cover(text):
    """Drop the 8-K cover page; start at the first 'Item x.xx' heading after it."""
    m = re.search(r"Item\s+\d\.\d\d\.?\s", text[1500:], re.I)
    return text[1500 + m.start():] if m else text


def _cut_signature(text):
    m = re.search(r"\bSIGNATURES?\b\s+Pursuant to the requirements", text, re.I)
    return text[: m.start()] if m else text


def _filing_base(cik, acc):
    return f"https://www.sec.gov/Archives/edgar/data/{cik}/{acc.replace('-', '')}"


def _exhibit_99(cik, acc):
    try:
        idx = get(_filing_base(cik, acc) + "/index.json", sec=True, as_json=True)
    except Exception:
        return None, None
    for f in idx["directory"]["item"]:
        n = f["name"].lower()
        if "99" in n and ("ex" in n) and not n.startswith("r"):
            if n.endswith((".htm", ".html", ".txt")):
                url = _filing_base(cik, acc) + "/" + f["name"]
                return url, _clean(get(url, sec=True))
    return None, None


def _form4_summary(cik, acc, doc):
    raw = doc.split("/")[-1]
    try:
        xml = get(_filing_base(cik, acc) + "/" + raw, sec=True)
        root = ET.fromstring(xml)
    except Exception:
        return None
    owner = root.findtext(".//reportingOwner/reportingOwnerId/rptOwnerName") or "an insider"
    title = root.findtext(".//reportingOwner/reportingOwnerRelationship/officerTitle") or ""
    parts = []
    for t in root.findall(".//nonDerivativeTable/nonDerivativeTransaction"):
        code = t.findtext("./transactionCoding/transactionCode") or "?"
        shares = t.findtext("./transactionAmounts/transactionShares/value") or "?"
        price = t.findtext("./transactionAmounts/transactionPricePerShare/value") or ""
        date = t.findtext("./transactionDate/value") or ""
        desc = FORM4_CODES.get(code, f"code {code}")
        p = f" at ${float(price):,.2f}" if price and price.replace(".", "", 1).isdigit() else ""
        try:
            shares = f"{float(shares):,.0f}"
        except ValueError:
            pass
        parts.append(f"{date}: {desc} of {shares} shares{p}")
    if not parts:
        parts.append("derivative transactions only (options or units)")
    role = f" ({title})" if title else ""
    return f"Form 4 insider filing by {owner}{role}. Transactions: " + "; ".join(parts[:6]) + "."


def filings(ticker, start, end):
    """Return items for every filing dated start..end (inclusive, YYYY-MM-DD)."""
    cik, title = cik_for(ticker)
    sub = get(f"https://data.sec.gov/submissions/CIK{cik:010d}.json", sec=True, as_json=True)
    rec = sub["filings"]["recent"]
    items = []
    for i, form in enumerate(rec["form"]):
        date = rec["filingDate"][i]
        if not (start <= date <= end):
            continue
        acc, doc = rec["accessionNumber"][i], rec["primaryDocument"][i]
        url = f"{_filing_base(cik, acc)}/{doc}"
        base = {"source": "SEC EDGAR", "kind": form, "date": date, "url": url}
        if form in ("8-K", "8-K/A"):
            codes = [c for c in rec["items"][i].split(",") if c]
            names = [f"Item {c} {ITEM_NAMES.get(c, '')}".strip() for c in codes]
            body = _cut_signature(_strip_cover(_clean(get(url, sec=True))))
            items.append({**base, "title": f"{title} 8-K: " + "; ".join(names), "text": body[:MAX_CHARS]})
            ex_url, ex = _exhibit_99(cik, acc)
            if ex and len(ex) > 400:
                items.append({**base, "kind": "8-K exhibit 99.1", "url": ex_url,
                              "title": f"{title} 8-K exhibit 99.1 (press release)", "text": ex[:MAX_CHARS]})
        elif form == "4":
            s = _form4_summary(cik, acc, doc)
            if s:
                items.append({**base, "title": f"{title} Form 4", "text": s})
        elif form in ("10-Q", "10-K"):
            body = _clean(get(url, sec=True))
            heads = list(re.finditer(r"Item\s+[27]\.?\s+Management.s Discussion and Analysis", body, re.I))
            # the first match is usually the table of contents; use the last one
            excerpt = body[heads[-1].start():] if heads else body[3000:]
            items.append({**base, "title": f"{title} {form} (MD&A excerpt)", "text": excerpt[:MAX_CHARS]})
        else:
            desc = rec.get("primaryDocDescription", [""] * len(rec["form"]))[i] or form
            items.append({**base, "title": f"{title} {form}", "text": f"{title} filed a {form} ({desc}) on {date}."})
    return items
