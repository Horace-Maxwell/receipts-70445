# Changelog

Every change to the prompt, the source check or the scoring is logged here with the date and the reason.

## 2026-11-18
- v0.1: first version; 10 test cases and pass rules locked in commit 2bd6ca5 before any run.
- verify.py: digits inside terms the prompt itself defines ("S&P 500", "20 trading days", "8-K", "Item 5.02",
  "12-1") are no longer treated as numbers that need a source. Found on the first 6 midpoint answers: 3 of them
  failed only because the summary said "S&P 500". The pass rules and expected answers did not change.
