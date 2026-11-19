"""News: GDELT for a past window (no key), Yahoo Finance RSS for the latest headlines (no key)."""
import html
import time
import re
import xml.etree.ElementTree as ET
from datetime import datetime

from bs4 import BeautifulSoup

from ..config import COMPANIES
from ..http import get


def _lead(url):
    """Best-effort one-paragraph summary from the article's meta description."""
    try:
        soup = BeautifulSoup(get(url, timeout=10), "html.parser")
    except Exception:
        return ""
    for attr in ({"property": "og:description"}, {"name": "description"}, {"name": "twitter:description"}):
        tag = soup.find("meta", attrs=attr)
        if tag and tag.get("content"):
            return html.unescape(tag["content"]).strip()
    return ""


def gdelt(ticker, start, end, max_items=8):
    q = COMPANIES[ticker]["news"] + " sourcelang:english sourcecountry:US"
    params = {"query": q, "mode": "artlist", "maxrecords": 40, "format": "json", "sort": "hybridrel",
              "startdatetime": start.replace("-", "") + "000000", "enddatetime": end.replace("-", "") + "235959"}
    data = {}
    for attempt in range(5):
        try:
            data = get("https://api.gdeltproject.org/api/v2/doc/doc", params=params, min_gap=6, as_json=True)
            break
        except Exception:
            time.sleep(12)
    seen, items = set(), []
    for a in data.get("articles", []):
        title = re.sub(r"\s+([,.;:!?])", r"\1", a["title"]).strip()
        if re.search(r"/(category|tag|tags|topic|topics|quote|quotes)/", a["url"]) or "latest news" in title.lower():
            continue
        key = re.sub(r"\W+", "", title.lower())[:60]
        if key in seen:
            continue
        seen.add(key)
        lead = _lead(a["url"])
        date = datetime.strptime(a["seendate"][:8], "%Y%m%d").strftime("%Y-%m-%d")
        text = title + (". " + lead if lead and lead.lower() not in title.lower() else "")
        items.append({"source": f"News ({a['domain']})", "kind": "news", "date": date, "url": a["url"],
                      "title": title, "text": text})
        if len(items) >= max_items:
            break
    return items


def yahoo_latest(ticker, max_items=10):
    xml = get("https://feeds.finance.yahoo.com/rss/2.0/headline", params={"s": ticker, "region": "US", "lang": "en-US"},
              cache=False)
    items = []
    for it in ET.fromstring(xml).iter("item"):
        title = (it.findtext("title") or "").strip()
        desc = BeautifulSoup(it.findtext("description") or "", "html.parser").get_text(" ").strip()
        try:
            date = datetime.strptime(it.findtext("pubDate")[:25], "%a, %d %b %Y %H:%M:%S").strftime("%Y-%m-%d")
        except Exception:
            date = ""
        items.append({"source": "News (Yahoo Finance)", "kind": "news", "date": date, "url": it.findtext("link"),
                      "title": title, "text": title + (". " + desc if desc else "")})
        if len(items) >= max_items:
            break
    return items
