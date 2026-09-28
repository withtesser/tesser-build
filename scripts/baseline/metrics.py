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
import json
import os
import pathlib
import re
import subprocess
import xml.etree.ElementTree as ET

TREE = "story-drafting"
FINDING = re.compile(r":\d+: (TB\d{3}) ")
TESSERCHECK_COMMAND = re.compile(r"tessercheck|srv\.cli\.main|scripts/verify")


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


def transcript_metrics(events: list[dict]) -> dict:
    tool_calls: collections.Counter[str] = collections.Counter()
    uses: dict[str, dict] = {}
    results: dict[str, str] = {}
    guidance: list[str] = []
    models: set[str] = set()
    final: dict = {}
    for event in events:
        kind = event.get("type")
        if kind == "system" and event.get("subtype") == "init":
            if event.get("model"):
                models.add(event["model"])
        elif kind == "assistant":
            message = event.get("message", {})
            if message.get("model"):
                models.add(message["model"])
            for part in message.get("content", []):
                if part.get("type") == "tool_use":
                    tool_calls[part["name"]] += 1
                    uses[part["id"]] = part
                    tool_input = part.get("input", {})
                    if part["name"] == "Skill":
                        guidance.append(f"skill:{tool_input.get('skill')}")
                    elif part["name"] == "Read" and "skills/tesser-build/" in str(tool_input.get("file_path", "")):
                        guidance.append(f"read:{pathlib.Path(tool_input['file_path']).name}")
        elif kind == "user":
            for part in event.get("message", {}).get("content", []):
                if isinstance(part, dict) and part.get("type") == "tool_result":
                    results[part["tool_use_id"]] = result_text(part.get("content"))
        elif kind == "result":
            final = event

    runs = []
    for use_id, use in uses.items():
        if use["name"] != "Bash":
            continue
        command = str(use.get("input", {}).get("command", ""))
        if not TESSERCHECK_COMMAND.search(command):
            continue
        codes = collections.Counter(FINDING.findall(results.get(use_id, "")))
        runs.append({"command": command[:200], "findings": sum(codes.values()), "by_code": dict(codes)})

    usage = final.get("usage", {})
    return {
        "models": sorted(models),
        "result_subtype": final.get("subtype"),
        "is_error": final.get("is_error"),
        "duration_s": round(final.get("duration_ms", 0) / 1000, 1),
        "duration_api_s": round(final.get("duration_api_ms", 0) / 1000, 1),
        "num_turns": final.get("num_turns"),
        "cost_usd": final.get("total_cost_usd"),
        "tokens": {
            "input": usage.get("input_tokens"),
            "output": usage.get("output_tokens"),
            "cache_read": usage.get("cache_read_input_tokens"),
            "cache_write": usage.get("cache_creation_input_tokens"),
        },
        "tool_calls_total": sum(tool_calls.values()),
        "tool_calls": dict(tool_calls.most_common()),
        "guidance": guidance,
        "tessercheck_runs": runs,
        "tessercheck_runs_count": len(runs),
        "final_message": str(final.get("result", ""))[:2000],
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


def gate_metrics(worktree: pathlib.Path, out: pathlib.Path) -> dict:
    coverage = out / "coverage.json"
    junit = out / "junit.xml"
    env = dict(os.environ)
    env["PYTEST_ADDOPTS"] = f"--cov=. --cov-report=json:{coverage} --junitxml={junit} -p no:cacheprovider"
    proc = subprocess.run(["scripts/verify", TREE], cwd=worktree, env=env, capture_output=True, text=True)
    (out / "verify.log").write_text(proc.stdout + proc.stderr)
    log = proc.stdout
    steps = re.findall(r"→ (.+)", log)
    tessercheck_findings = len(FINDING.findall(log))

    tests = []
    if junit.exists():
        for case in ET.parse(junit).getroot().iter("testcase"):
            outcome, message = "passed", ""
            for tag in ("failure", "error", "skipped"):
                node = case.find(tag)
                if node is not None:
                    outcome = {"failure": "failed", "error": "error", "skipped": "skipped"}[tag]
                    message = (node.get("message") or node.text or "")[:500]
                    break
            tests.append({"id": f"{case.get('classname')}::{case.get('name')}", "outcome": outcome, "message": message})

    covered = total = 0
    if coverage.exists():
        for path, data in json.loads(coverage.read_text()).get("files", {}).items():
            if is_test(path):
                continue
            covered += data["summary"]["covered_lines"]
            total += data["summary"]["num_statements"]
    outcomes = collections.Counter(t["outcome"] for t in tests)
    return {
        "verify_exit": proc.returncode,
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
    parser.add_argument("--agent-exit", type=int, default=None)
    args = parser.parse_args()

    run = json.loads((args.out / "run.json").read_text())
    metrics = {
        "run": run,
        "agent_exit": args.agent_exit,
        "agent": transcript_metrics(read_jsonl(args.out / "transcript.jsonl")),
        "hook": hook_metrics(read_jsonl(args.out / "hook-changes.jsonl")),
        "diff": diff_metrics(args.worktree, args.base),
        "gate": gate_metrics(args.worktree, args.out),
    }
    (args.out / "metrics.json").write_text(json.dumps(metrics, indent=2) + "\n")

    agent, hook, diff, gate = metrics["agent"], metrics["hook"], metrics["diff"], metrics["gate"]
    print(f"phase {args.phase}: agent exit {args.agent_exit}, {agent['duration_s']}s, {agent['num_turns']} turns, "
          f"{agent['tool_calls_total']} tool calls, ${agent['cost_usd']}")
    print(f"  tessercheck runs by agent: {agent['tessercheck_runs_count']}, findings per run: "
          f"{[r['findings'] for r in agent['tessercheck_runs']]}")
    print(f"  hook: {hook['analyzed_writes']} analyzed writes, {hook['writes_with_findings']} with findings, "
          f"{hook['findings_total']} findings, by code {hook['findings_by_code']}")
    print(f"  diff: {diff['commits']} commits, {diff['files_changed']} files, impl {diff['py_impl_files']} files/"
          f"{diff['py_impl_lines']} lines, tests {diff['py_test_files']} files/{diff['py_test_lines']} lines, "
          f"uncommitted {len(diff['uncommitted'])}")
    print(f"  gate: verify exit {gate['verify_exit']}, final tessercheck findings {gate['tessercheck_findings']}, "
          f"tests {gate['test_outcomes']}, impl coverage {gate['impl_coverage_pct']}%")
    for test in gate["tests"]:
        if test["outcome"] != "passed":
            print(f"    {test['outcome']}: {test['id']}: {test['message'][:200]}")


if __name__ == "__main__":
    main()
