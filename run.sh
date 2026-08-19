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
  # Local model runs need an Anthropic-Messages-compatible server already
  # serving the model (e.g. mlx-dspark). Point these at yours:
  #   LOCAL_BASE_URL   default http://127.0.0.1:8080
  #   LOCAL_MODEL_ID   default Qwen3.8-27B-8bit (must match /v1/models)
  # Or set LOCAL_LAUNCHER to a command that wraps claude with your own
  # launcher (the recorded runs used a strict-local wrapper equivalent to
  # the env-based invocation below, plus offline-irrelevant web-tool config).
  if [ -n "${LOCAL_LAUNCHER:-}" ]; then
    $LOCAL_LAUNCHER --dangerously-skip-permissions \
      -p "$PROMPT" --output-format json > agent-output.json 2> agent-stderr.log
  else
    LOCAL_BASE_URL="${LOCAL_BASE_URL:-http://127.0.0.1:8080}"
    LOCAL_MODEL_ID="${LOCAL_MODEL_ID:-Qwen3.8-27B-8bit}"
    env -u ANTHROPIC_API_KEY \
      ANTHROPIC_BASE_URL="$LOCAL_BASE_URL" \
      ANTHROPIC_AUTH_TOKEN="local-only" \
      ANTHROPIC_MODEL="$LOCAL_MODEL_ID" \
      ANTHROPIC_SMALL_FAST_MODEL="$LOCAL_MODEL_ID" \
      CLAUDE_CODE_ENABLE_GATEWAY_MODEL_DISCOVERY="0" \
      claude --model "$LOCAL_MODEL_ID" --dangerously-skip-permissions \
      -p "$PROMPT" --output-format json > agent-output.json 2> agent-stderr.log
  fi
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
