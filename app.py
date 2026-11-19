"""Receipts web page.  Run locally with:  streamlit run app.py"""
import json
import os
from pathlib import Path

import streamlit as st

ROOT = Path(__file__).resolve().parent
try:  # Streamlit Cloud secrets -> environment, before receipts.config reads it
    for k in ("RECEIPTS_ANTHROPIC_API_KEY", "RECEIPTS_LLM_BACKEND", "SEC_USER_AGENT", "RECEIPTS_MODEL"):
        if k in st.secrets:
            os.environ[k] = str(st.secrets[k])
except Exception:
    pass

from receipts import agent  # noqa: E402
from receipts.config import ANTHROPIC_KEY, CASES_DIR, COMPANIES, WATCHLIST  # noqa: E402
from receipts.packet import collect, load, number, week_window  # noqa: E402
from receipts.collect import prices  # noqa: E402

st.set_page_config(page_title="Receipts", layout="wide")
st.title("Receipts")
st.caption("Weekly, sourced briefs on a stock watchlist. Research only: no trading, no price targets, "
           "no advice. A person reads the brief and makes the decision.")

MAX_LIVE_RUNS = 3


def show_brief(brief, items):
    by_id = {it["id"]: it for it in items}
    c1, c2, c3 = st.columns(3)
    c1.metric("Call vs. S&P 500, next 20 trading days", brief.get("call", "?"))
    c2.metric("Confidence", f"{brief.get('confidence', '?')}%")
    chk = brief.get("_check", {})
    c3.metric("Source check", "passed" if chk.get("passed") else "FAILED")
    st.write(brief.get("summary", ""))
    if not chk.get("passed"):
        for p in chk.get("attempts", [{}])[-1].get("problems", []):
            st.error(p)

    def src(iid):
        it = by_id.get(iid)
        if not it:
            return f"`{iid}` (unknown)"
        return f"[{it['source']}, {it['date']}]({it['url']}) `{iid}`"

    st.subheader("What matters this week")
    if not brief.get("flags"):
        st.write("Nothing material found.")
    for f in brief.get("flags", []):
        tag = "CRITICAL · " if f.get("critical") else ""
        st.markdown(f"**{tag}{f.get('direction', '')}**: {f.get('why', '')}  \n> {f.get('quote', '')}  \n{src(f.get('item_id'))}")
    a, b = st.columns(2)
    with a:
        st.subheader("Evidence for the call")
        for e in brief.get("evidence_for", []):
            st.markdown(f"- {e.get('claim')}  \n  > {e.get('quote')}  \n  {src(e.get('item_id'))}")
    with b:
        st.subheader("Evidence against")
        for e in brief.get("evidence_against", []):
            st.markdown(f"- {e.get('claim')}  \n  > {e.get('quote')}  \n  {src(e.get('item_id'))}")
    st.markdown(f"**What would change the call:** {brief.get('would_change_call', '')}")
    if brief.get("suspicious_items"):
        st.warning("Documents that tried to instruct the agent: " +
                   "; ".join(f"{s.get('item_id')}: {s.get('why')}" for s in brief["suspicious_items"]))
    if brief.get("ignored"):
        st.caption("Ignored: " + ", ".join(f"{i.get('item_id')} ({i.get('reason')})" for i in brief["ignored"]))
    with st.expander(f"All {len(items)} source documents"):
        for it in items:
            st.markdown(f"**`{it['id']}` {it['title']}** · {it['source']} · {it['date']} · [link]({it['url']})")
            st.text(it["text"][:3000])


tab_watch, tab_tests, tab_run, tab_about = st.tabs(["Watchlist briefs", "Test cases", "Run a brief", "About"])

with tab_watch:
    weeks = sorted([p for p in (ROOT / "briefs").iterdir() if p.is_dir() and any(p.glob("*.json"))],
                   reverse=True) if (ROOT / "briefs").exists() else []
    if not weeks:
        st.info("No watchlist briefs yet.")
    else:
        wk = st.selectbox("Week of", weeks, format_func=lambda p: p.name)
        files = sorted(wk.glob("*.json"))
        rows = []
        for f in files:
            b = json.loads(f.read_text())
            rows.append({"Ticker": f.stem, "Call": b.get("call"), "Confidence": b.get("confidence"),
                         "Material items": len(b.get("flags", [])),
                         "Critical": sum(bool(x.get("critical")) for x in b.get("flags", []))})
        st.dataframe(rows, hide_index=True, use_container_width=True)
        pick = st.selectbox("Open a brief", [f.stem for f in files])
        b = json.loads((wk / f"{pick}.json").read_text())
        _, items = load(wk / "packets" / pick)
        show_brief(b, items)

with tab_tests:
    res = ROOT / "results" / "midpoint"
    if (res / "REPORT.md").exists():
        st.markdown((res / "REPORT.md").read_text())
    cases = sorted(p for p in CASES_DIR.iterdir() if p.is_dir())
    case = st.selectbox("Test case", cases, format_func=lambda p: p.name)
    run = st.radio("Run", [1, 2, 3], horizontal=True)
    exp = json.loads((case / "expected.json").read_text()) if (case / "expected.json").exists() else {}
    st.caption("Expected material events: " + "; ".join(
        f"{e['name']} ({', '.join(e['items'])}){' [critical]' if e['critical'] else ''}" for e in exp.get("events", [])) or "none")
    bf = res / "briefs" / f"{case.name}__r{run}.json"
    _, items = load(case)
    if bf.exists():
        show_brief(json.loads(bf.read_text()), items)
    else:
        st.info("This run has no result yet.")

with tab_run:
    st.write("Build a fresh brief for any watchlist stock and week. This calls the model and the public data sources live, "
             "so it takes about a minute.")
    if not ANTHROPIC_KEY:
        st.warning("Live runs are switched off on this deployment (no model API key configured). "
                   "The Watchlist and Test case tabs show briefs the same code produced.")
    else:
        t = st.selectbox("Stock", WATCHLIST + [k for k in COMPANIES if k not in WATCHLIST])
        monday = st.date_input("Brief date (a Monday; covers the week before)")
        n = st.session_state.get("live_runs", 0)
        if st.button("Run", disabled=n >= MAX_LIVE_RUNS):
            if monday.weekday() != 0:
                st.error("Pick a Monday.")
            else:
                st.session_state["live_runs"] = n + 1
                start, end = week_window(monday.isoformat())
                with st.spinner("Collecting documents..."):
                    items = number(collect(t, start, end), t)
                    meta = {"ticker": t, "window_start": start, "window_end": end, "features": prices.features(t, end)}
                with st.spinner(f"Reading {len(items)} documents..."):
                    brief = agent.run(meta, items, f"live_{t}_{monday}", backend="anthropic")
                show_brief(brief, items)
        st.caption(f"{MAX_LIVE_RUNS} live runs per visitor.")

with tab_about:
    st.markdown((ROOT / "README.md").read_text())
