#!/bin/bash
# Assemble a blinded review package: per task, the prompt, the baseline code,
# and the two agents' diffs labelled Agent A / Agent B with a randomized
# mapping per task. The mapping lands in results/blind-key.json, which the
# blinded reviewer must never read. No timings, costs, or model IDs.
set -eu
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BLIND="${BLIND_DIR:-$ROOT/results/blind}"
TASKS="${TASKS:-ratelimiter retry todo-cli}"
rm -rf "$BLIND"
mkdir -p "$BLIND"
KEY="${KEY_FILE:-$ROOT/results/blind-key.json}"
printf '{\n' > "$KEY"
first=true

full_diff() {
  # Tracked changes plus files the agent added, minus run artifacts.
  # Reset first so stale staging from earlier tooling can't leak in.
  git -C "$1" reset -q HEAD -- . >/dev/null 2>&1 || true
  git -C "$1" add -A -- \
    ':!agent-output.json' ':!agent-stderr.log' ':!wall-seconds.txt' \
    ':!agent-exit-status.txt' ':!visible-tests.log' ':!holdout.log' \
    ':!diff-stat.txt' ':!todo.json' ':!*.log' \
    ':(exclude)__pycache__' ':(exclude)*.pyc' >/dev/null 2>&1
  # The committed results/blind/ package predates the __pycache__ exclusion
  # and is kept byte-identical to what the blinded reviewer saw.
  git -C "$1" diff --cached HEAD
}

for task in $TASKS; do
  mkdir -p "$BLIND/$task"
  {
    echo "# Task: $task"
    echo
    echo "## Prompt given to both agents"
    echo
    cat "$ROOT/tasks/$task/prompt.txt"
    echo
    echo "## Baseline project (before either agent ran)"
    for f in "$ROOT/tasks/$task/workspace/"*.py; do
      echo
      echo "### $(basename "$f")"
      echo '```python'
      cat "$f"
      echo '```'
    done
  } > "$BLIND/$task/task.md"

  if [ $((RANDOM % 2)) -eq 0 ]; then a="qwen"; b="opus-max"; else a="opus-max"; b="qwen"; fi
  full_diff "$ROOT/runs/$task-$a" > "$BLIND/$task/agent-a.diff"
  full_diff "$ROOT/runs/$task-$b" > "$BLIND/$task/agent-b.diff"
  $first || printf ',\n' >> "$KEY"
  first=false
  printf '  "%s": {"agent-a": "%s", "agent-b": "%s"}' "$task" "$a" "$b" >> "$KEY"
done
printf '\n}\n' >> "$KEY"
echo "blinded package at $BLIND (key: $KEY — do not show the reviewer)"
