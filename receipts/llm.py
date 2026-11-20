"""Model backends.

anthropic: calls the Anthropic API with RECEIPTS_ANTHROPIC_API_KEY.
relay:     writes the prompt to relay/requests/<id>.md and reads relay/responses/<id>.json.
           Used before the team had an API key: an operator (Claude Code subagents) answered each request
           in a fresh context with the same prompt. Same code path, different transport.
"""
import json
import os
import re

from .config import ANTHROPIC_KEY, ANTHROPIC_MODEL, LLM_BACKEND, RELAY_DIR


class Pending(Exception):
    """The relay has not answered this request yet."""


def complete(request_id, system, user, backend=None):
    backend = backend or LLM_BACKEND
    if backend == "anthropic":
        return _anthropic(system, user)
    if backend == "relay":
        return _relay(request_id, system, user)
    raise ValueError(backend)


def _anthropic(system, user):
    import anthropic
    key = os.environ.get("RECEIPTS_ANTHROPIC_API_KEY") or ANTHROPIC_KEY  # read at call time, not import time
    if not key:
        raise RuntimeError("Set RECEIPTS_ANTHROPIC_API_KEY in .env")
    client = anthropic.Anthropic(api_key=key, base_url="https://api.anthropic.com")
    msg = client.messages.create(model=os.environ.get("RECEIPTS_MODEL") or ANTHROPIC_MODEL, max_tokens=8000, system=system,
                                 messages=[{"role": "user", "content": user}])
    return "".join(b.text for b in msg.content if getattr(b, "type", "") == "text")


def _relay(request_id, system, user):
    req = RELAY_DIR / "requests" / f"{request_id}.md"
    resp = RELAY_DIR / "responses" / f"{request_id}.json"
    if resp.exists():
        return resp.read_text()
    req.parent.mkdir(parents=True, exist_ok=True)
    req.write_text("# SYSTEM\n\n" + system + "\n\n# USER\n\n" + user + "\n")
    raise Pending(request_id)


def parse_json(text):
    text = text.strip()
    m = re.search(r"\{.*\}", text, re.S)
    if not m:
        raise ValueError("no JSON object in model output")
    return json.loads(m.group(0))
