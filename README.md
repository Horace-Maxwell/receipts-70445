# Receipts

Team Signal & Noise (Horace Dong, Kevin Wang). 70-445, Final Project, Product Management track.

Every Monday, Receipts reads last week's SEC filings, news, macro data and Federal Register notices for each
stock on a watchlist and writes a short brief: a call versus the S&P 500 over the next 20 trading days
(Bullish, Neutral or Bearish), a confidence level, the items that matter, and the evidence on both sides.
Every quote links to its source and is checked by code. A person reads the brief and makes the decision.

**What it will not do:** trade, see any account, give price targets or position sizes, or tell you what to do.

## For reviewers (no install needed)

Open the web page and use the tabs:

1. **Watchlist briefs**: this week's briefs for 10 large stocks. Open one and check any quote against its source link.
2. **Test cases**: the 10 locked test cases, the expected answers, and what the agent actually wrote in each of 3 runs.
   The results table and every failure, quoted verbatim, are at the top.
3. **Run a brief**: build a fresh brief for any listed stock and week (only when a model key is configured).

Things worth trying to break: a week with a CEO exit, a week with nothing going on, and whether the brief
ever says something its quote does not support.

## How it works

```
collect   SEC EDGAR (8-K text and press release, Form 4, 10-Q/10-K MD&A) · news (GDELT; Yahoo for live) ·
          FRED macro snapshot · Federal Register rules            -> numbered items
quant     5-day and 21-day return, excess return vs SPY, 12-1 momentum, 20-day volatility (code, not the model)
model     one call: reads every item, flags material ones, writes the call and the evidence as JSON
check     every quote must appear verbatim in its cited item; every number must be in the quote or price inputs;
          on failure the model gets the list of problems and one retry
```

The prompt is in `receipts/prompt.py`; the source check is in `receipts/verify.py`.

## Running it yourself

```bash
pip install -r requirements.txt
cp .env.example .env          # add RECEIPTS_ANTHROPIC_API_KEY and set RECEIPTS_LLM_BACKEND=anthropic
streamlit run app.py
python -m eval.run --runs 3 --tag mytest     # rerun the test set
```

## Tests

`eval/CRITERIA.md` holds the pass rules, written before the first run. Each case folder in `eval/cases/` holds
the documents (`items.jsonl`), the price inputs (`packet.json`), the expected answer (`expected.json`) and the
planted traps (`traps.json`, never shown to the agent). Results are in `results/midpoint/`.

## Data sources

All public, no accounts, no API keys.

| Source | Used for | Endpoint |
|---|---|---|
| SEC EDGAR | 8-K text and press releases, Form 4, 10-Q/10-K | https://www.sec.gov/search-filings/edgar-application-programming-interfaces |
| GDELT DOC 2.0 | News for past weeks | https://api.gdeltproject.org/api/v2/doc/doc ([docs](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)) |
| Yahoo Finance RSS | News for the current week | https://feeds.finance.yahoo.com/rss/2.0/headline (unofficial, undocumented) |
| Yahoo Finance chart | Daily adjusted closes for the stock and SPY | https://query1.finance.yahoo.com/v8/finance/chart/ (unofficial, undocumented) |
| FRED | Macro snapshot (frozen, see RUNBOOK) | https://fred.stlouisfed.org/ |
| Federal Register | Rules matching the company's sector (frozen) | https://www.federalregister.gov/developers/documentation/api/v1 |

The proposal named Finnhub or Alpha Vantage for news and Alpaca for prices. We switched to GDELT and Yahoo
because they need no key and cover past weeks, which the test cases need.

## For the team

`RUNBOOK.md` explains how to run the weekly briefs and the tests, how to add a case, and how to change the
prompt or the check. It also holds our plan for making sure either of us can run and change the pipeline.

Research and education only. Not investment advice.
