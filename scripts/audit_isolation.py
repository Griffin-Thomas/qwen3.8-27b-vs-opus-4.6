#!/usr/bin/env python3
"""Audit run transcripts for cross-contamination.

Scans each run's Claude Code session transcript for tool calls that reach
outside the run's own directory: the sibling model's run dir, the holdout
graders under tasks/, or any parent-directory traversal. Prints every hit
with its tool and argument so a human can judge it.
"""

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROJECTS = Path.home() / ".claude" / "projects"
RUNS = sorted(p.name for p in (ROOT / "runs").iterdir() if p.is_dir())

SUSPICIOUS = [
    (re.compile(r"\.\./"), "parent traversal"),
    (re.compile(r"\bholdout\b"), "holdout reference"),
    (re.compile(r"/tasks/"), "task-definition dir"),
    (re.compile(r"\btasks/(ratelimiter|retry|todo-cli)\b"), "task-definition dir"),
]


def encode(path):
    return re.sub(r"[/.]", "-", str(path))


def check(run):
    run_dir = ROOT / "runs" / run
    proj = PROJECTS / encode(run_dir)
    hits, calls = [], 0
    for jsonl in sorted(proj.glob("*.jsonl")):
        for line in jsonl.open():
            try:
                d = json.loads(line)
            except json.JSONDecodeError:
                continue
            if d.get("type") != "assistant":
                continue
            for block in d.get("message", {}).get("content", []):
                if block.get("type") != "tool_use":
                    continue
                calls += 1
                arg = json.dumps(block.get("input", {}))
                # Any runs/ path that isn't this run's own directory.
                for ref in re.findall(r"runs/([\w.-]+)", arg):
                    if ref != run:
                        hits.append((block["name"], f"sibling run {ref}", arg[:160]))
                for pat, label in SUSPICIOUS:
                    if pat.search(arg):
                        hits.append((block["name"], label, arg[:160]))
    return calls, hits


def main():
    clean = True
    for run in RUNS:
        calls, hits = check(run)
        print(f"== {run}: {calls} tool calls, {len(hits)} flagged")
        for tool, label, arg in hits:
            clean = False
            print(f"   [{label}] {tool}: {arg}")
    print("VERDICT:", "clean — no run touched holdouts, task defs, or sibling runs"
          if clean else "flags above need human review")


if __name__ == "__main__":
    main()
