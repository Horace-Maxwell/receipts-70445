# Changelog

Every change to the prompt, the source check or the scoring is logged here with the date and the reason.

## 2026-11-18
- v0.1: first version; 10 test cases and pass rules locked in commit 2bd6ca5 before any run.
- verify.py: digits inside terms the prompt itself defines ("S&P 500", "20 trading days", "8-K", "Item 5.02",
  "12-1") are no longer treated as numbers that need a source. Found on the first 6 midpoint answers: 3 of them
  failed only because the summary said "S&P 500". The pass rules and expected answers did not change.
- edgar.py: when a company files more than 3 of the same routine form in a week (424B2, FWP, 13G, Form 4, ...),
  the rest are merged into one summary item. JPMorgan's week of Nov 9 had 408 items, mostly note supplements.
  The Nov 16 JPM brief was made before this change.
