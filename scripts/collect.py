#!/usr/bin/env python3
"""Collect per-run metrics into results/summary.json."""

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASKS = ["ratelimiter", "retry", "todo-cli"]
MODELS = ["qwen", "opus", "opus-max"]


def last_json_line(path):
    """The qwen launcher prints banner lines around claude's JSON output."""
    result = None
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("{"):
            try:
                result = json.loads(line)
            except json.JSONDecodeError:
                continue
    return result


def holdout_counts(path):
    text = path.read_text()
    ran = re.search(r"Ran (\d+) tests?", text)
    total = int(ran.group(1)) if ran else 0
    if re.search(r"^OK", text, re.M):
        return total, total
    failed = len(re.findall(r"^(FAIL|ERROR):", text, re.M))
    return total - failed, total


def main():
    summary = {}
    for task in TASKS:
        for model in MODELS:
            run = ROOT / "runs" / f"{task}-{model}"
            if not (run / "holdout.log").exists():
                continue
            passed, total = holdout_counts(run / "holdout.log")
            agent = last_json_line(run / "agent-output.json") or {}
            visible = (run / "visible-tests.log").read_text()
            summary[f"{task}-{model}"] = {
                "holdout_passed": passed,
                "holdout_total": total,
                "visible_tests_ok": "\nOK" in visible or visible.startswith("OK"),
                "wall_seconds": int((run / "wall-seconds.txt").read_text().strip()),
                "num_turns": agent.get("num_turns"),
                "duration_api_ms": agent.get("duration_api_ms"),
                "usage": agent.get("usage"),
                "total_cost_usd": agent.get("total_cost_usd"),
                "is_error": agent.get("is_error"),
                "diff_stat": (run / "diff-stat.txt").read_text().strip(),
            }
    out = ROOT / "results" / "summary.json"
    out.write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
