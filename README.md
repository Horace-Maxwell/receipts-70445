# Receipts

**Weekly, sourced stock briefs for a student-managed fund analyst. Every quote links to its source and is checked by code.**

**[Open the live page →](https://receipts-70445.streamlit.app/)** (public, no login; if Streamlit says the app is asleep, click "Yes, get this app back up!" and wait ~30 s)

Team Signal & Noise (Horace Dong, Kevin Wang) · 70-445 AI for Business Leaders, Carnegie Mellon · Final Project, Product Management track

Every Monday, Receipts reads last week's SEC filings and news for each stock on a 10-stock watchlist and writes a
short brief: a call versus the S&P 500 over the next 20 trading days (Bullish, Neutral or Bearish), a confidence
level, the items that matter, and the evidence on both sides. A person reads the brief and makes the decision.

**What it will not do:** trade, see any account, give price targets or position sizes, or tell you what to do.

| Midpoint test (10 locked cases × 3 runs) | Result |
|---|---|
| Flags ≥90% of material events and every critical one | 27/27 event-runs; the 4 critical events in all 12 runs |
| Every quote and number matches its source | 30/30 briefs |
| Ignores planted instructions | 15/15 runs |
| Same call in at least 2 of 3 runs | 10/10 cases |

All four pre-registered criteria passed and all 10 cases were hits, which mainly tells us the cases are too easy. How the runs were done (a manual relay, not the API) and other limits are in the midpoint package and on the page. The final set will be adversarial.

## For reviewers (no install needed)

On the [live page](https://receipts-70445.streamlit.app/):

1. **Watchlist briefs.** Click "Open brief" on any stock card. Check a quote against its source link, or against the
   full document under "All source documents".
2. **Test results.** The pass rules and results, all 10 cases, and every failure quoted verbatim. In the Case explorer,
   pick a case and run to see the expected events, the traps we planted and exactly what the agent wrote.
   Start with C01 NVDA (CEO exit plus a planted instruction) and C09 JNJ (a quiet week with traps).
3. **Run a brief.** Pick any listed stock and a recent week and run the agent live (3 runs per visit, 1–2 minutes each).

What we most want found: a claim its quote does not support, a material item the brief missed, a call that does not
follow from its evidence, or an expected answer of ours that looks wrong.

## How it works

```
collect   SEC EDGAR (8-K text and press release, Form 4, 10-Q/10-K MD&A) · news (GDELT) ·
          FRED macro snapshot · Federal Register rules            -> numbered items
quant     5-day and 21-day return, excess return vs SPY, 12-1 momentum, 20-day volatility (code, not the model)
model     one call: reads every item, flags material ones, writes the call and the evidence as JSON
check     every quote must appear verbatim in its cited item; every number must be in the quote or price inputs;
          on failure the model gets the list of problems and one retry
```

The prompt is in `receipts/prompt.py`; the source check is in `receipts/verify.py`.

## Running it yourself

No API key is needed to check our results:

```bash
pip install -r requirements.txt
cp .env.example .env                          # put your own name and email in SEC_USER_AGENT
python -m eval.run --runs 3 --tag midpoint    # re-scores the stored answers; prints "agent_passes": true
git checkout -- results/midpoint              # the rerun only changes a timestamp
streamlit run app.py                          # the web page, locally
```

To run new briefs you need a model key: set `RECEIPTS_ANTHROPIC_API_KEY` and `RECEIPTS_LLM_BACKEND=anthropic` in
`.env`. Without a key, the default `relay` backend only writes prompts to `relay/requests/` (see RUNBOOK.md).

## Tests

`eval/CRITERIA.md` holds the pass rules, written before the first run (committed in one batch with the code; see the errata file for one wrong count). Each case folder in `eval/cases/` holds
the documents (`items.jsonl`), the price inputs (`packet.json`), the expected answer (`expected.json`) and the
planted traps (`traps.json`, never shown to the agent). Results are in `results/midpoint/`.

## Data sources

All public, no accounts, no API keys.

| Source | Used for | Endpoint |
|---|---|---|
| SEC EDGAR | 8-K text and press releases, Form 4, 10-Q/10-K | https://www.sec.gov/search-filings/edgar-application-programming-interfaces |
| GDELT DOC 2.0 | News | https://api.gdeltproject.org/api/v2/doc/doc ([docs](https://blog.gdeltproject.org/gdelt-doc-2-0-api-debuts/)) |
| Yahoo Finance chart | Daily adjusted closes for the stock and SPY | https://query1.finance.yahoo.com/v8/finance/chart/ (unofficial, undocumented) |
| FRED | Macro snapshot (frozen, see RUNBOOK) | https://fred.stlouisfed.org/ |
| Federal Register | Rules matching the company's sector (frozen) | https://www.federalregister.gov/developers/documentation/api/v1 |

The proposal named Finnhub or Alpha Vantage for news and Alpaca for prices. We switched to GDELT and Yahoo
because they need no key and cover past weeks, which the test cases need. (`news.py` also has a Yahoo Finance RSS function for current headlines,
but no current code path calls it.)

## For the team

`RUNBOOK.md` explains how to run the weekly briefs and the tests, how to add a case, and how to change the
prompt or the check. It also holds our plan for making sure either of us can run and change the pipeline.

Research and education only. Not investment advice.
