#!/usr/bin/env python3
"""The shared black-box check for the story-drafting A/B experiment.

Starts one arm's output as a served process, registers its Restate endpoint
with the run's Restate server (arm B may have none; that is recorded, not
fatal), and runs the two level-2 stories over HTTP, tolerant of everything
the specs leave open: an id of any shape, extra keys, and how long drafting
takes (it polls until the status reads awaiting_story_acceptance or the
timeout passes). It asserts only what story.toml says, and prints one JSON
document.

    check.py --cwd DIR --cmd "python3 -m srv.http.main 0.0.0.0:9300" \\
             --port 9300 --admin http://localhost:39070 \\
             --env RESTATE_INGRESS=http://localhost:38080 [--env K=V ...]
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request

ROLE, I_WANT, SO_THAT = "a developer", "my work to survive across sessions", "I can pick up where I left off"


def call(method: str, url: str, body: dict[str, object] | None = None, timeout: float = 30) -> tuple[int, object, str]:
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as answer:
            status, raw = answer.status, answer.read()
    except urllib.error.HTTPError as error:
        status, raw = error.code, error.read()
    except (urllib.error.URLError, TimeoutError, ConnectionError, OSError) as error:
        return 0, None, f"{type(error).__name__}: {error}"
    text = raw.decode(errors="replace")
    try:
        return status, json.loads(text), text
    except json.JSONDecodeError:
        return status, None, text


def wait_for_port(host: str, port: int, seconds: float) -> float | None:
    started = time.monotonic()
    while time.monotonic() - started < seconds:
        status, _, _ = call("GET", f"http://{host}:{port}/", timeout=2)
        if status != 0:
            return round(time.monotonic() - started, 2)
        time.sleep(0.25)
    return None


def register(admin: str, callback_host: str, port: int) -> dict[str, object]:
    status, _, text = call("POST", f"{admin}/deployments", {"uri": f"http://{callback_host}:{port}/restate", "force": True})
    return {"ok": 200 <= status < 300, "status": status, "detail": text[:300]}


def story_1(base: str) -> tuple[dict[str, object], str | None]:
    status, body, text = call("POST", f"{base}/jtbds", {"role": ROLE, "i_want": I_WANT, "so_that": SO_THAT})
    problems = []
    if status != 201:
        problems.append(f"status {status}, wanted 201")
    jtbd_id = body.get("jtbd_id") if isinstance(body, dict) else None
    if jtbd_id in (None, "", 0):
        problems.append("no jtbd_id")
    if not isinstance(body, dict) or body.get("status") != "drafting_stories":
        problems.append(f"status field {body.get('status') if isinstance(body, dict) else None!r}, wanted 'drafting_stories'")
    return {"passed": not problems, "problems": problems, "answered": text[:300]}, None if jtbd_id in (None, "") else str(jtbd_id)


def story_2(base: str, jtbd_id: str | None, seconds: float) -> dict[str, object]:
    if jtbd_id is None:
        return {"passed": False, "problems": ["no jtbd_id to read (story 1 gave none)"]}
    started = time.monotonic()
    status, body, text = 0, None, ""
    while True:
        status, body, text = call("GET", f"{base}/jtbds/{jtbd_id}")
        if isinstance(body, dict) and body.get("status") == "awaiting_story_acceptance":
            break
        if time.monotonic() - started > seconds:
            break
        time.sleep(0.25)
    waited = round(time.monotonic() - started, 2)
    problems = []
    if status != 200:
        problems.append(f"status {status}, wanted 200")
    if not isinstance(body, dict) or body.get("status") != "awaiting_story_acceptance":
        problems.append(f"status field {body.get('status') if isinstance(body, dict) else None!r} after {waited}s, wanted 'awaiting_story_acceptance'")
    stories = body.get("stories") if isinstance(body, dict) else None
    if not isinstance(stories, list) or not stories:
        problems.append("no stories")
    else:
        for index, story in enumerate(stories):
            if not isinstance(story, dict):
                problems.append(f"story {index} is not an object")
                continue
            for key in ("given", "when", "then"):
                if not isinstance(story.get(key), str) or not story[key].strip():
                    problems.append(f"story {index} has no non-empty {key}")
            if story.get("state") != "drafted":
                problems.append(f"story {index} state {story.get('state')!r}, wanted 'drafted'")
    return {"passed": not problems, "problems": problems, "seconds_until_drafted": waited, "answered": text[:600]}


def probes(base: str) -> dict[str, object]:
    """Observed, never scored: what the specs leave open."""
    unknown, _, _ = call("GET", f"{base}/jtbds/does-not-exist")
    missing, _, _ = call("POST", f"{base}/jtbds", {"role": ROLE})
    return {"get_unknown_id_status": unknown, "post_missing_fields_status": missing}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cwd", required=True)
    parser.add_argument("--cmd", required=True)
    parser.add_argument("--port", required=True, type=int)
    parser.add_argument("--admin", required=True)
    parser.add_argument("--callback-host", default="host.docker.internal")
    parser.add_argument("--env", action="append", default=[])
    parser.add_argument("--start-seconds", type=float, default=60)
    parser.add_argument("--draft-seconds", type=float, default=30)
    parser.add_argument("--log", required=True)
    args = parser.parse_args()

    env = dict(os.environ)
    env["PORT"] = str(args.port)
    for pair in args.env:
        key, _, value = pair.partition("=")
        env[key] = value
    result: dict[str, object] = {"cmd": args.cmd, "cwd": args.cwd}
    with open(args.log, "w") as log:
        host = subprocess.Popen(shlex.split(args.cmd), cwd=args.cwd, env=env, stdout=log, stderr=subprocess.STDOUT,
                                start_new_session=True)
        try:
            base = f"http://127.0.0.1:{args.port}"
            started = wait_for_port("127.0.0.1", args.port, args.start_seconds)
            result["seconds_to_listen"] = started
            if started is None:
                result.update(served=False, story_1={"passed": False, "problems": ["never listened"]},
                              story_2={"passed": False, "problems": ["never listened"]})
            else:
                result["served"] = True
                result["restate_registration"] = register(args.admin, args.callback_host, args.port)
                story1, jtbd_id = story_1(base)
                result["story_1"] = story1
                result["story_2"] = story_2(base, jtbd_id, args.draft_seconds)
                result["probes"] = probes(base)
            result["exited_early"] = host.poll() is not None
        finally:
            try:
                os.killpg(host.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            host.wait()
    result["passed"] = bool(result.get("story_1", {}).get("passed") and result.get("story_2", {}).get("passed"))  # type: ignore[union-attr]
    json.dump(result, sys.stdout, indent=2)
    print()
    sys.exit(0 if result["passed"] else 1)


if __name__ == "__main__":
    main()
