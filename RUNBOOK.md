# Runbook: how to run and change Receipts

This file exists so that either of us can run, fix and change the pipeline without the other. It answers
the professor's proposal feedback: "Consider a plan for sharing pipeline knowledge so either of you can run
and change it." If a step here is wrong or missing, fix this file in the same commit as the fix.

## 0. One-time setup (about 10 minutes)

```bash
git clone https://github.com/Horace-Maxwell/receipts-70445.git
cd receipts-70445
python3 -m pip install -r requirements.txt
cp .env.example .env        # set SEC_USER_AGENT to your own name and Andrew email (SEC requires one)
```

Leave `RECEIPTS_LLM_BACKEND=relay` until we have an API key. With a key, set `RECEIPTS_LLM_BACKEND=anthropic`
and `RECEIPTS_ANTHROPIC_API_KEY=...`. Never commit `.env`.

Smoke test, no network or model needed. This re-scores the stored midpoint answers and must print
`"agent_passes": true`:

```bash
python3 -m eval.run --runs 3 --tag midpoint
git checkout -- results/midpoint     # the rerun only changes the timestamp; throw that away
```

## 1. The pipeline in one screen

| Step | File | What it does | Owner / second owner |
|---|---|---|---|
| Collect | `receipts/collect/edgar.py` | 8-Ks, press releases, Form 4, 10-Q/10-K text from SEC EDGAR; merges repeated routine filings | Horace / Kevin |
| Collect | `receipts/collect/news.py` | GDELT news (1 request per ~5 s); a Yahoo RSS function exists but is not called | Horace / Kevin |
| Collect | `receipts/collect/prices.py` | Yahoo Finance daily closes; 5-day and 21-day return, excess vs SPY, 12-1 momentum, 20-day vol | Horace / Kevin |
| Collect | `receipts/collect/macro.py` | FRED snapshot, Federal Register rules (frozen, see section 5) | Horace |
| Packet | `receipts/packet.py` | Numbers every item (`NVDA-07`), saves `items.jsonl` + `packet.json` | Horace / Kevin |
| Model | `receipts/prompt.py`, `receipts/agent.py`, `receipts/llm.py` | One model call writes the brief as JSON; on a failed check, one retry with the list of problems | Horace / Kevin |
| Check | `receipts/verify.py` | Every quote verbatim in its cited item; every number in the quote or the price inputs | Horace / Kevin |
| Tests | `eval/build_cases.py`, `eval/run.py`, `eval/CRITERIA.md` | Builds the locked cases with planted traps; runs and scores them | Kevin / Horace |
| Page | `app.py` | Streamlit page: watchlist briefs, test cases, run a brief | Horace / Kevin |

"Second owner" is the person who must be able to change that file alone by the final (see section 6). Most of the code
was drafted with Claude Code and reviewed by Horace; the owner is the person responsible for it, not its typist.

## 2. Weekly briefs (every Monday)

```bash
python3 -m receipts.weekly --monday 2026-11-23
```

- With `anthropic`: one pass. Briefs land in `briefs/2026-11-23/<TICKER>.json`.
- With `relay`: the first run collects the packets and writes one prompt per stock to `relay/requests/`.
  Each prompt is answered in a fresh model session and saved as `relay/responses/<same name>.json`.
  Then run the same command again; it reads the answers, runs the check and writes the briefs.
  A retry shows up as a new request ending in `__a2`; answer it and run once more.
- Then: `streamlit run app.py`, open the new week, skim every brief, commit
  `briefs/<monday>/` and `relay/` with the message "Watchlist briefs for week of <monday>".

## 3. Test cases

- Re-score stored answers: `python3 -m eval.run --runs 3 --tag midpoint`. The tag must match the stored
  answers in `relay/responses/`; a new tag writes new requests instead of scoring.
- New run of the test set (for example the final): `python3 -m eval.run --runs 3 --tag final`.
- **Adding a case** (the final set): add a row to `CASES` in `eval/build_cases.py`, run
  `python3 -m eval.build_cases`, then write `eval/cases/<case>/expected.json` by hand from the filings.
  Commit the case folder **before** any model sees it, and put the commit hash in the results write-up.
- Never edit `eval/CRITERIA.md` or an `expected.json` after results exist. Add a dated file instead
  (see `eval/ERRATA-2026-11-20.md`).

## 4. Changing the prompt, the check or the scoring

1. Make the change on a branch and open a pull request; the other person reviews it before merge.
2. Add a dated line to `CHANGELOG.md`: what changed, why, and which result made us change it.
3. Re-run the smoke test in section 0. If the change touches `verify.py` or `prompt.py`, say in the PR
   whether the stored midpoint results would change.

## 5. Known traps

- **GDELT rate limit.** About one request every five seconds; above that it returns errors and a week can
  end up with no news, with no error shown (news errors are caught and skipped). `news.py` waits 6 seconds between calls. If a packet has zero news items,
  delete the packet folder and re-run that ticker alone (`--tickers BA`).
- **Cache.** Every HTTP response is cached in `data/cache/` (not in git). Delete a file there to force a refetch.
- **SEC.** EDGAR blocks requests without a real `SEC_USER_AGENT`.
- **Yahoo Finance** endpoints are unofficial and undocumented. A price error is not caught: the weekly run
  stops with a traceback at that ticker. Wait and re-run; finished tickers are skipped because their packets exist.
- **Frozen sources.** FRED and Federal Register stay as they are: we do not fix or extend them before the
  final. In 40 briefs (30 test runs, 10 watchlist briefs) they produced 2 of 46 flags. If either breaks, remove it from `packet.py` and log it.

## 6. Knowledge-sharing plan (team charter addendum, Nov 20)

| What | Who | By when |
|---|---|---|
| Kevin is a collaborator on the GitHub repo and has run the smoke test from a clean clone | Kevin | Sat Nov 21 |
| 30-minute walkthrough of one pipeline file at the start of each Monday and Thursday meeting, led by the file's second owner, not its author | both | each meeting |
| Kevin runs the Nov 23 weekly briefs alone from this runbook; Horace only answers questions in writing, and any gap becomes a fix to this file | Kevin | Mon Nov 23 |
| Kevin makes the first real pipeline change: tighten the summary-number check in `verify.py` (known weakness 4), by pull request reviewed by Horace | Kevin | Sat Nov 28 |
| Horace builds and labels two of the final test cases, so he knows the case side too | Horace | Sat Nov 28 |
| Check: each of us, alone, runs the final test set from a clean clone and gets the same summary | both | Wed Dec 2 |
