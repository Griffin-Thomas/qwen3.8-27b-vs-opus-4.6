#!/bin/bash
# Run one agent on one task and grade it against the held-out tests.
# Usage: ./run.sh <task> <qwen|opus-max>
set -u
ROOT="$(cd "$(dirname "$0")" && pwd)"
TASK="$1"
MODEL="$2"
RUN="$ROOT/runs/$TASK-$MODEL"

rm -rf "$RUN"
mkdir -p "$RUN"
cp "$ROOT/tasks/$TASK/workspace/"* "$RUN/"
cd "$RUN" || exit 1
git init -q && git add -A && git commit -qm baseline

PROMPT="$(cat "$ROOT/tasks/$TASK/prompt.txt")"
START="$(date +%s)"
if [ "$MODEL" = "qwen" ]; then
  /Users/griffin/AI/qwen3.8-27b/qwen local --dangerously-skip-permissions \
    -p "$PROMPT" --output-format json > agent-output.json 2> agent-stderr.log
elif [ "$MODEL" = "opus-max" ]; then
  env -u ANTHROPIC_API_KEY -u ANTHROPIC_AUTH_TOKEN -u ANTHROPIC_BASE_URL -u ANTHROPIC_MODEL \
    claude --model claude-opus-4-6 --effort max --dangerously-skip-permissions \
    -p "$PROMPT" --output-format json > agent-output.json 2> agent-stderr.log
else
  echo "unknown model: $MODEL (use qwen or opus-max)" >&2
  exit 2
fi
STATUS=$?
END="$(date +%s)"
echo "$((END - START))" > wall-seconds.txt
echo "$STATUS" > agent-exit-status.txt

# Visible tests as the agent left them.
python3 -m unittest -q > visible-tests.log 2>&1
echo "$?" >> visible-tests.log

# Held-out grading: drop the holdout suite into the project exactly as the
# agent left it, so imports resolve the same way they did for the agent.
cp "$ROOT/tasks/$TASK/holdout/"*.py "$RUN/"
HOLDOUT_MODULE="$(basename "$ROOT/tasks/$TASK/holdout/"*.py .py)"
python3 -m unittest -v "$HOLDOUT_MODULE" > holdout.log 2>&1
rm -f "$RUN/$HOLDOUT_MODULE.py"
git diff --stat HEAD > diff-stat.txt 2>/dev/null
git status --short >> diff-stat.txt
echo "run complete: $TASK-$MODEL, $((END - START))s"
