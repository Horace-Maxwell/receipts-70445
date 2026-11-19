"""One brief: packet -> prompt -> model -> source check -> (one retry) -> brief."""
import json

from . import llm, prompt, verify


def run(meta, items, request_id, backend=None):
    """Return a brief dict. Raises llm.Pending if the relay has not answered yet."""
    attempts = []
    feedback = None
    for attempt in (1, 2):
        rid = f"{request_id}__a{attempt}"
        raw = llm.complete(rid, prompt.SYSTEM, prompt.render(meta, items, feedback), backend)
        try:
            brief = llm.parse_json(raw)
            problems = verify.check(brief, items, meta.get("features", {}))
        except (ValueError, json.JSONDecodeError) as e:
            brief, problems = {}, [f"output was not valid JSON: {e}"]
        attempts.append({"attempt": attempt, "problems": problems})
        if not problems:
            break
        feedback = problems
    brief["_check"] = {"passed": not problems, "attempts": attempts, "prompt_version": prompt.PROMPT_VERSION}
    return brief
