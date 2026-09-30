"""Measure one baseline run: the agent's transcript, the hook's change log, and
the tree the agent left behind.

Writes metrics.json into the run's output directory and prints a summary.
The end-state gate is scripts/verify story-drafting, run with coverage and a
JUnit report added through PYTEST_ADDOPTS, so the measured pytest run is the
same one the gate runs.
"""

from __future__ import annotations

import argparse
import collections
import datetime
import hashlib
import json
import os
import pathlib
import re
import signal
import subprocess

TREE = "story-drafting"
GATE_TIMEOUT_S = 600  # a gate that has not finished by then is hung; it is killed and recorded as such
FINDING = re.compile(r":\d+: (TB\d{3}) ")
SUMMARY = re.compile(r"^(PASSED|FAILED|ERROR|SKIPPED|XFAIL|XPASS) (\S+)(?: - (.*))?$")
TESSERCHECK_COMMAND = re.compile(r"scripts/verify\s+[\w-]|scripts/verify\s*($|[;&|])|-m srv\.cli\.main|tessercheck-check|tessercheck_tree")
SKILL_DOC = re.compile(r"skills/tesser-build/([\w.-]+\.md)")


def read_jsonl(path: pathlib.Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line:
            try:
                rows.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return rows


def result_text(content: object) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(part.get("text", "") for part in content if isinstance(part, dict))
    return ""


# What a Bash call spent its time on, by the first rule its command matches:
# checking the work (the gate, tests, the analyzer, type and lint checks),
# setting up (a virtualenv, installs, containers), or exercising the served
# service by hand. Any other call, of any tool, is "other".
TIME_CLASSES = (
    ("checking", re.compile(r"scripts/verify|pytest|tessercheck|-m srv\.cli\.main|\bmypy\b|\bruff\b")),
    ("setup", re.compile(r"\bvenv\b|pip3? install|\buv (pip|sync|add|venv)|\bdocker\b")),
    ("probing", re.compile(r"\bcurl\b|main\.py|srv\.http")),
)


def union_s(spans: list[tuple[datetime.datetime, datetime.datetime]]) -> float:
    """Seconds covered by the spans, counting an overlap once: calls the agent
    makes in parallel share their wall-clock time."""
    covered, end = 0.0, None
    for start, stop in sorted(spans):
        if end is None or start > end:
            covered += (stop - start).total_seconds()
            end = stop
        elif stop > end:
            covered += (stop - end).total_seconds()
            end = stop
    return covered


def time_split(rows: list[dict]) -> dict:
    """The agent's wall-clock time, split by what it was waiting on. A tool
    call runs from its tool_use row to its tool_result row; the time in no
    call is the model's own (thinking and writing). Parallel calls count once,
    within a class and across classes (a moment in two classes counts in the
    first of checking, setup, probing, other)."""
    stamps: list[datetime.datetime] = []
    started: dict[str, tuple[datetime.datetime, str]] = {}
    spans: dict[str, list[tuple[datetime.datetime, datetime.datetime]]] = {name: [] for name, _ in TIME_CLASSES}
    spans["other"] = []
    for row in rows:
        if not row.get("timestamp"):
            continue
        stamp = datetime.datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00"))
        stamps.append(stamp)
        message = row.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), list):
            continue
        for part in message["content"]:
            if not isinstance(part, dict):
                continue
            if row.get("type") == "assistant" and part.get("type") == "tool_use":
                command = str(part.get("input", {}).get("command", "")) if part.get("name") == "Bash" else ""
                kind = next((name for name, pattern in TIME_CLASSES if command and pattern.search(command)), "other")
                started[part["id"]] = (stamp, kind)
            elif row.get("type") == "user" and part.get("type") == "tool_result" and part.get("tool_use_id") in started:
                begun, kind = started.pop(part["tool_use_id"])
                spans[kind].append((begun, stamp))
    if not stamps:
        return {}
    total = (max(stamps) - min(stamps)).total_seconds()
    split, claimed = {}, []
    for kind in ("checking", "setup", "probing", "other"):
        before = union_s(claimed)
        claimed = claimed + spans[kind]
        split[f"{kind}_s"] = round(union_s(claimed) - before, 1)
    split["model_s"] = round(total - union_s(claimed), 1)
    return split


def transcript_metrics(rows: list[dict]) -> dict:
    """A subagent transcript (session-log format): one row per content block,
    rows of one API request sharing a requestId and repeating its usage. The
    recorded usage is the first streamed chunk's, so output tokens are not
    counted: they read as a handful per request whatever was written."""
    tool_calls: collections.Counter[str] = collections.Counter()
    uses: dict[str, dict] = {}
    results: dict[str, str] = {}
    guidance: list[str] = []
    models: set[str] = set()
    usage_by_request: dict[str, dict] = {}
    stamps: list[datetime.datetime] = []
    final_text = ""
    for row in rows:
        if row.get("timestamp"):
            stamps.append(datetime.datetime.fromisoformat(row["timestamp"].replace("Z", "+00:00")))
        message = row.get("message")
        if not isinstance(message, dict):
            continue
        if row.get("type") == "assistant":
            if message.get("model"):
                models.add(message["model"])
            if row.get("requestId") and message.get("usage"):
                usage_by_request[row["requestId"]] = message["usage"]
            for part in message.get("content", []):
                if part.get("type") == "text" and part.get("text", "").strip():
                    final_text = part["text"]
                if part.get("type") != "tool_use":
                    continue
                tool_calls[part["name"]] += 1
                uses[part["id"]] = part
                tool_input = part.get("input", {})
                if part["name"] == "Skill":
                    guidance.append(f"skill:{tool_input.get('skill')}")
                elif part["name"] == "Read" and "skills/tesser-build/" in str(tool_input.get("file_path", "")):
                    guidance.append(f"read:{pathlib.Path(tool_input['file_path']).name}")
                elif part["name"] == "Bash":
                    guidance.extend(f"bash:{doc}" for doc in SKILL_DOC.findall(str(tool_input.get("command", ""))))
        elif row.get("type") == "user" and isinstance(message.get("content"), list):
            for part in message["content"]:
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    results[part["tool_use_id"]] = result_text(part.get("content"))

    runs = []
    for use_id, use in uses.items():
        if use["name"] != "Bash":
            continue
        command = str(use.get("input", {}).get("command", ""))
        if not TESSERCHECK_COMMAND.search(command):
            continue
        output = results.get(use_id, "")
        codes = collections.Counter(FINDING.findall(output))
        if not codes and "tessercheck (zero findings" not in output and "-m srv.cli.main" not in command and "tessercheck-check" not in command:
            continue
        runs.append({"command": command[:200], "findings": sum(codes.values()), "by_code": dict(codes)})

    def total(key: str) -> int:
        return sum(u.get(key) or 0 for u in usage_by_request.values())

    return {
        "models": sorted(models),
        "duration_s": round((max(stamps) - min(stamps)).total_seconds(), 1) if stamps else None,
        "time": time_split(rows),
        "api_requests": len(usage_by_request),
        "tokens": {
            "input": total("input_tokens"),
            "cache_read": total("cache_read_input_tokens"),
            "cache_write": total("cache_creation_input_tokens"),
        },
        "tool_calls_total": sum(tool_calls.values()),
        "tool_calls": dict(tool_calls.most_common()),
        "guidance": guidance,
        "tessercheck_runs": runs,
        "tessercheck_runs_count": len(runs),
        "final_message": final_text[:2000],
    }


def run_conditions(rows: list[dict], meta: dict) -> dict:
    """What the trial ran under, read from its own transcript rather than from
    what it was asked to run under: the effort each request recorded (a named
    teammate ignores an agent definition's effort, so the ask and the record
    can differ), how it was spawned, and which system prompt it got."""
    efforts = sorted({row["effort"] for row in rows if row.get("type") == "assistant" and row.get("effort")})
    snapshot = next(
        (
            row["attachment"]
            for row in rows
            if row.get("type") == "attachment"
            and isinstance(row.get("attachment"), dict)
            and row["attachment"].get("type") == "prompt_snapshot"
        ),
        None,
    )
    system_prompt = None
    if snapshot is not None:
        parts = snapshot.get("systemPrompt")
        text = "\n".join(parts) if isinstance(parts, list) else str(parts)
        system_prompt = {"chars": len(text), "sha256": hashlib.sha256(text.encode()).hexdigest()[:16]}
    return {
        "effort": efforts,
        "spawn": {
            "agent_type": meta.get("agentType"),
            "task_kind": meta.get("taskKind", "subagent") if meta else None,
            "model_requested": meta.get("model"),
        },
        "system_prompt": system_prompt,
    }


def hook_metrics(rows: list[dict]) -> dict:
    writes = [row for row in rows if row.get("source") == "write" and row.get("placement") == "governed"]
    codes: collections.Counter[str] = collections.Counter()
    for row in writes:
        for finding in row.get("findings", []):
            codes[finding.split(":", 1)[0]] += 1
    return {
        "analyzed_writes": len(writes),
        "writes_with_findings": sum(1 for row in writes if row.get("findings_count")),
        "findings_total": sum(row.get("findings_count", 0) for row in writes),
        "findings_by_code": dict(codes.most_common()),
        "findings_per_write": [row.get("findings_count", 0) for row in writes],
    }


def git(worktree: pathlib.Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=worktree, capture_output=True, text=True).stdout


class GitFailed(Exception):
    pass


def git_strict(worktree: pathlib.Path, *args: str) -> str:
    """Like git(), but a failed command raises instead of reading as empty output."""
    proc = subprocess.run(["git", *args], cwd=worktree, capture_output=True, text=True)
    if proc.returncode != 0:
        raise GitFailed(f"git {' '.join(args)}: {proc.stderr.strip() or proc.returncode}")
    return proc.stdout


def is_test(path: str) -> bool:
    name = pathlib.PurePosixPath(path).name
    return name.startswith("test_") or name == "conftest.py" or "/tests/" in f"/{path}"


def diff_metrics(worktree: pathlib.Path, base: str) -> dict:
    head = git(worktree, "rev-parse", "HEAD").strip()
    files = []
    for line in git(worktree, "diff", "--numstat", base, "HEAD").splitlines():
        added, removed, path = line.split("\t", 2)
        files.append({"path": path, "added": int(added) if added != "-" else 0, "removed": int(removed) if removed != "-" else 0})
    py = [f for f in files if f["path"].endswith(".py")]
    return {
        "head": head,
        "commits": len(git(worktree, "rev-list", f"{base}..HEAD").split()),
        "uncommitted": [line for line in git(worktree, "status", "--porcelain").splitlines() if ".tesser/" not in line],
        "files_changed": len(files),
        "lines_added": sum(f["added"] for f in files),
        "lines_removed": sum(f["removed"] for f in files),
        "py_impl_files": len([f for f in py if not is_test(f["path"])]),
        "py_impl_lines": sum(f["added"] for f in py if not is_test(f["path"])),
        "py_test_files": len([f for f in py if is_test(f["path"])]),
        "py_test_lines": sum(f["added"] for f in py if is_test(f["path"])),
        "files_outside_tree": [f["path"] for f in files if not f["path"].startswith(f"{TREE}/")],
    }


AGENT_OWNED = "# pragma: tesser-agent-owned;"
GREEN_PHASES = ("green-specs", "green-on-red")
PROTECTED_PREFIXES = (f"{TREE}/specs/", "generator/compositions/", f"{TREE}/tests/")
PROTECTED_FILES = ("scripts/verify", f"{TREE}/.tesser-rendered")
# Ignored files are counted, because pytest collects a gitignored conftest.py
# as readily as a tracked one. Only what the tools themselves write is exempt.
TOOL_DIRS = ("__pycache__", ".tesser", ".mypy_cache", ".pytest_cache", ".ruff_cache", ".hypothesis")
TOOL_FILES = (".coverage", "coverage.json")


def integrity_metrics(worktree: pathlib.Path, base: str, phase: str) -> dict:
    """What a green trial changed against what it was allowed to change.

    The render drift check only compares generated files with the specs, so
    it cannot see a trial that edits the specs and re-renders, weakens an
    acceptance test, or deletes a file it owns. This compares the trial's
    commit and working tree with its base: the files it may change are the
    ones marked agent-owned at the base, plus new domain modules; the specs,
    acceptance tests, verify script, render marker, and any .tesser-root must
    be byte-identical.
    """
    if phase not in GREEN_PHASES:
        return {"checked": False}
    try:
        return audit_integrity(worktree, base)
    except GitFailed as failure:
        return {"checked": True, "ok": False, "error": str(failure)}


def is_tool_output(path: str) -> bool:
    parts = pathlib.PurePosixPath(path).parts
    return any(part in TOOL_DIRS for part in parts) or parts[-1] in TOOL_FILES or path.endswith(".pyc")


def audit_integrity(worktree: pathlib.Path, base: str) -> dict:
    git_strict(worktree, "rev-parse", "--verify", f"{base}^{{commit}}")
    at_base = git_strict(worktree, "ls-tree", "-r", "--name-only", base).splitlines()
    owned = {path for path in at_base if path.endswith(".py")
             and AGENT_OWNED in git_strict(worktree, "show", f"{base}:{path}")[:400]}
    changes: dict[str, str] = {}
    for line in git_strict(worktree, "diff", "--name-status", "--no-renames", base).splitlines():
        status, path = line.split("\t", 1)
        changes[path] = status
    untracked = git_strict(worktree, "ls-files", "--others", "--exclude-standard").splitlines()
    ignored = git_strict(worktree, "ls-files", "--others", "--ignored", "--exclude-standard").splitlines()
    for line in untracked + ignored:
        changes.setdefault(line, "A")
    changes = {path: status for path, status in changes.items() if not is_tool_output(path)}

    def new_domain_module(path: str, status: str) -> bool:
        parts = pathlib.PurePosixPath(path).parts
        return status == "A" and path.endswith(".py") and len(parts) >= 3 and parts[0] == TREE and parts[-2] == "domain"

    protected = sorted(path for path in changes if path.startswith(PROTECTED_PREFIXES) or path in PROTECTED_FILES
                       or pathlib.PurePosixPath(path).name == ".tesser-root")
    outside = sorted(path for path, status in changes.items()
                     if path not in owned and not new_domain_module(path, status) and path not in protected)
    owned_deleted = sorted(path for path, status in changes.items() if path in owned and status == "D")
    return {
        "checked": True,
        "owned_at_base": sorted(owned),
        "changed": sorted(changes),
        "protected_changed": protected,
        "outside_owned": outside,
        "owned_deleted": owned_deleted,
        "ok": not (protected or outside or owned_deleted),
    }


def gate_metrics(worktree: pathlib.Path, out: pathlib.Path) -> dict:
    coverage = out / "coverage.json"
    env = dict(os.environ)
    run = json.loads((out / "run.json").read_text())
    if "engine_url" in run:
        env["RESTATE_URL"] = run["engine_url"]
        env["RESTATE_ADMIN"] = run["restate_admin"]
        env["STORY_DRAFTING_PORT"] = str(run["host_port"])
    env["COVERAGE_FILE"] = str(out / ".coverage")
    env["PYTEST_ADDOPTS"] = f"--cov=. --cov-append --cov-report=json:{coverage} -rA -p no:cacheprovider"
    # The gate runs in its own process group with its output in a file, not a
    # pipe: a served host that outlives the script (a gate that aborts before
    # stopping it) would otherwise hold the pipe open and hang this run, and
    # would stay running. Whatever the script leaves in its group is killed.
    with (out / "verify.log").open("w") as log_file:
        proc = subprocess.Popen(["scripts/verify", TREE], cwd=worktree, env=env, stdout=log_file,
                                stderr=subprocess.STDOUT, start_new_session=True)
        try:
            verify_exit = proc.wait(timeout=GATE_TIMEOUT_S)
        except subprocess.TimeoutExpired:
            verify_exit = "timeout"
    try:
        os.killpg(proc.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    log = (out / "verify.log").read_text()
    steps = re.findall(r"→ (.+)", log)
    tessercheck_findings = len(FINDING.findall(log))

    tests = []
    for line in log.splitlines():
        outcome = SUMMARY.match(line)
        if outcome:
            tests.append({
                "id": outcome.group(2),
                "outcome": outcome.group(1).lower(),
                "message": (outcome.group(3) or "")[:500],
            })

    covered = total = 0
    if coverage.exists():
        for path, data in json.loads(coverage.read_text()).get("files", {}).items():
            if is_test(path):
                continue
            covered += data["summary"]["covered_lines"]
            total += data["summary"]["num_statements"]
    outcomes = collections.Counter(t["outcome"] for t in tests)
    return {
        "verify_exit": verify_exit,
        "verify_steps_reached": steps,
        "tessercheck_findings": tessercheck_findings,
        "tests": tests,
        "test_outcomes": dict(outcomes),
        "impl_coverage_pct": round(100 * covered / total, 1) if total else None,
        "impl_statements": total,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--phase", required=True)
    parser.add_argument("--worktree", required=True, type=pathlib.Path)
    parser.add_argument("--base", required=True)
    parser.add_argument("--out", required=True, type=pathlib.Path)
    parser.add_argument("--integrity-only", action="store_true",
                        help="re-audit an already measured run and replace only its integrity block")
    args = parser.parse_args()

    if args.integrity_only:
        measured = json.loads((args.out / "metrics.json").read_text())
        measured["integrity"] = integrity_metrics(args.worktree, args.base, args.phase)
        (args.out / "metrics.json").write_text(json.dumps(measured, indent=2) + "\n")
        print(f"integrity: {'ok' if measured['integrity'].get('ok') else 'VIOLATED'}: {json.dumps(measured['integrity'])[:300]}")
        return

    run = json.loads((args.out / "run.json").read_text())
    transcript = read_jsonl(args.out / "transcript.jsonl")
    meta_path = args.out / "transcript.meta.json"
    meta = json.loads(meta_path.read_text()) if meta_path.is_file() else {}
    metrics = {
        "run": run,
        "conditions": run_conditions(transcript, meta),
        "agent": transcript_metrics(transcript),
        "hook": hook_metrics(read_jsonl(args.out / "hook-changes.jsonl")),
        "diff": diff_metrics(args.worktree, args.base),
        "integrity": integrity_metrics(args.worktree, args.base, args.phase),
        "gate": gate_metrics(args.worktree, args.out),
    }
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")

    agent, hook, diff, gate = metrics["agent"], metrics["hook"], metrics["diff"], metrics["gate"]
    print(f"phase {args.phase}: {agent['duration_s']}s, {agent['api_requests']} API requests, "
          f"{agent['tool_calls_total']} tool calls {agent['tool_calls']}, tokens {agent['tokens']}, models {agent['models']}")
    print(f"  time: {agent['time']}")
    print(f"  guidance: {agent['guidance']}")
    print(f"  tessercheck runs by agent: {agent['tessercheck_runs_count']}, findings per run: "
          f"{[r['findings'] for r in agent['tessercheck_runs']]}")
    print(f"  hook: {hook['analyzed_writes']} analyzed writes, {hook['writes_with_findings']} with findings, "
          f"{hook['findings_total']} findings, by code {hook['findings_by_code']}")
    print(f"  diff: {diff['commits']} commits, {diff['files_changed']} files, impl {diff['py_impl_files']} files/"
          f"{diff['py_impl_lines']} lines, tests {diff['py_test_files']} files/{diff['py_test_lines']} lines, "
          f"uncommitted {len(diff['uncommitted'])}")
    integrity = metrics["integrity"]
    if integrity.get("error"):
        print(f"  integrity: VIOLATED; the audit could not run: {integrity['error']}")
    elif integrity["checked"]:
        print(f"  integrity: {'ok' if integrity['ok'] else 'VIOLATED'}; changed {len(integrity['changed'])} files, "
              f"outside owned {integrity['outside_owned']}, protected changed {integrity['protected_changed']}, "
              f"owned deleted {integrity['owned_deleted']}")
    print(f"  gate: verify exit {gate['verify_exit']}, final tessercheck findings {gate['tessercheck_findings']}, "
          f"tests {gate['test_outcomes']}, impl coverage {gate['impl_coverage_pct']}%")
    for test in gate["tests"]:
        if test["outcome"] != "passed":
            print(f"    {test['outcome']}: {test['id']}: {test['message'][:200]}")


if __name__ == "__main__":
    main()
