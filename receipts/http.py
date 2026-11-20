"""HTTP helper with a polite rate limit and a disk cache."""
import hashlib
import json
import os
import time

import requests

from .config import CACHE_DIR, SEC_USER_AGENT

_last = {}
BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) Receipts/0.1"


def get(url, params=None, sec=False, min_gap=0.0, timeout=25, cache=True, as_json=False):
    """GET a URL and return text (or parsed JSON). Results are cached on disk."""
    key = hashlib.sha1((url + json.dumps(params or {}, sort_keys=True)).encode()).hexdigest()
    path = CACHE_DIR / key[:2] / key
    if cache and path.exists():
        text = path.read_text()
    else:
        host = url.split("/")[2]
        gap = 0.12 if sec else min_gap
        wait = _last.get(host, 0) + gap - time.time()
        if wait > 0:
            time.sleep(wait)
        headers = {"User-Agent": (os.environ.get("SEC_USER_AGENT") or SEC_USER_AGENT) if sec else BROWSER_UA}
        r = requests.get(url, params=params, headers=headers, timeout=timeout)
        _last[host] = time.time()
        r.raise_for_status()
        text = r.text
        if as_json:
            json.loads(text)  # raises before a non-JSON reply (e.g. a rate-limit notice) is cached
        if cache:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(text)
    return json.loads(text) if as_json else text
