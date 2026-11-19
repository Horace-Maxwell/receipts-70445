"""Settings, paths and the watchlist."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _load_dotenv():
    env = ROOT / ".env"
    if not env.exists():
        return
    for line in env.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv()

SEC_USER_AGENT = os.environ.get("SEC_USER_AGENT", "Receipts student project contact@example.com")
LLM_BACKEND = os.environ.get("RECEIPTS_LLM_BACKEND", "relay")  # "anthropic" or "relay"
ANTHROPIC_KEY = os.environ.get("RECEIPTS_ANTHROPIC_API_KEY", "")
ANTHROPIC_MODEL = os.environ.get("RECEIPTS_MODEL", "claude-sonnet-5-5")
FINNHUB_KEY = os.environ.get("FINNHUB_API_KEY", "")

CACHE_DIR = ROOT / "data" / "cache"
CASES_DIR = ROOT / "eval" / "cases"
BRIEFS_DIR = ROOT / "briefs"
RELAY_DIR = ROOT / "relay"
RESULTS_DIR = ROOT / "results"

# News search terms (GDELT) and a policy keyword (Federal Register) per ticker.
COMPANIES = {
    "AAPL": {"name": "Apple", "news": '"Apple" (iPhone OR "Tim Cook" OR "Apple Inc")', "policy": "smartphone"},
    "MSFT": {"name": "Microsoft", "news": '"Microsoft"', "policy": "cloud computing"},
    "NVDA": {"name": "Nvidia", "news": '"Nvidia"', "policy": "semiconductor export"},
    "AMZN": {"name": "Amazon", "news": '"Amazon" (AWS OR "Amazon.com" OR Jassy)', "policy": "e-commerce"},
    "JPM": {"name": "JPMorgan Chase", "news": '"JPMorgan"', "policy": "bank capital"},
    "XOM": {"name": "Exxon Mobil", "news": '"Exxon"', "policy": "crude oil"},
    "JNJ": {"name": "Johnson & Johnson", "news": '"Johnson & Johnson"', "policy": "drug pricing"},
    "WMT": {"name": "Walmart", "news": '"Walmart"', "policy": "tariff"},
    "BA": {"name": "Boeing", "news": '"Boeing"', "policy": "aircraft"},
    "PFE": {"name": "Pfizer", "news": '"Pfizer"', "policy": "drug pricing"},
    # Test-case companies
    "COO": {"name": "The Cooper Companies", "news": '"Cooper Companies" OR "CooperCompanies"', "policy": "medical device"},
    "CHTR": {"name": "Charter Communications", "news": '"Charter Communications"', "policy": "broadband"},
    "AZO": {"name": "AutoZone", "news": '"AutoZone"', "policy": "auto parts"},
    "BSX": {"name": "Boston Scientific", "news": '"Boston Scientific"', "policy": "medical device"},
    "NKE": {"name": "Nike", "news": '"Nike" (shares OR sneaker OR footwear OR Hill)', "policy": "tariff"},
    "EQT": {"name": "EQT Corporation", "news": '"EQT" ("natural gas" OR Range)', "policy": "natural gas"},
    "GM": {"name": "General Motors", "news": '"General Motors"', "policy": "vehicle emissions"},
    "PTC": {"name": "PTC Inc.", "news": '"PTC" (software OR "Schneider Electric")', "policy": "industrial software"},
}

WATCHLIST = ["AAPL", "MSFT", "NVDA", "AMZN", "JPM", "XOM", "JNJ", "WMT", "BA", "PFE"]
