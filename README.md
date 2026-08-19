# qwen-vs-opus

An empirical head-to-head between a local open-weight model and a frontier
cloud model on realistic agentic coding tasks, run with the same harness, the
same prompts, and graded by held-out tests neither model ever sees.

- **Local**: Qwen3.8-27B, 8-bit MLX, running fully offline on a MacBook Pro
  (M5 Pro, 64 GB) with DSpark speculative decoding, driven by Claude Code
  through an Anthropic-compatible loopback server.
- **Cloud**: Claude Opus 4.6 (`claude-opus-4-6`), driven by the same Claude
  Code harness.

## Why

Vendor benchmarks put Qwen3.8-27B near Opus 4.6 on agentic coding
(SWE-bench Pro et al.). Those are the vendor's numbers, at unstated thinking
budgets, on benchmark harnesses. This repo asks a smaller, more honest
question: on small, realistic tasks with a little ambiguity, does the local
model actually hold up in the identical day-to-day harness?

## Tasks

Each task is a small self-contained Python project with a realistic defect or
feature request, a prompt written like a real bug report, and visible tests
that pass on the broken code (as shipped bugs usually do).

| Task | What the agent faces | Planted reality |
|---|---|---|
| `ratelimiter` | 2 confirmed customer reports against a sliding-window limiter | Rejected attempts are recorded (permanent lockout); timestamps truncated to whole seconds (boundary bursts) |
| `retry` | Ambiguous feature request: add retry with exponential backoff, "use your judgment" | Judgment graded on retryable-status choices, bounded attempts, growing delays |
| `todo-cli` | Bug report: completed tasks reappear as pending after restart | Enum serialized as `str(Status.DONE)` in one file, silently coerced to PENDING by a defensive loader in another |

## Grading

Each task ships a hidden holdout test suite the agents never see. The harness
was validated 3 ways before any agent ran: visible tests pass on pristine
code, holdout tests fail on pristine code, and holdout tests pass on
independently written reference fixes.

Recorded per run: holdout pass/fail per test, visible-test state as the agent
left it, wall-clock seconds, the agent's own usage report, and the diff.

## Protocol and fairness notes

- Same prompts, same Claude Code harness, same permission mode
  (`--dangerously-skip-permissions`), non-interactive print mode, one run per
  task per model. The prompts instruct the agents to work autonomously.
- The tasks are offline; neither agent needs or uses web access.
- Qwen runs at its daily-driver settings (8-bit, `REASONING_EFFORT=medium`,
  128K context) rather than benchmark-maximum thinking budgets. Opus 4.6 runs
  at Claude Code defaults. This intentionally compares the models as actually
  used, not as benchmarked.
- Wall-clock for the local model includes its real prefill costs; the server
  is started once before the runs so model-load time is excluded.
- One run per cell, so treat small differences as noise; the interesting
  signal is holdout outcomes and the diffs.
- Disclosure: the experiment was orchestrated by Claude (Fable 5) in Claude
  Code. Grading is mechanical (held-out unittest suites) precisely so no
  model judges its own family's work.

## Reproduce

```bash
./run.sh ratelimiter qwen   # or: retry, todo-cli
./run.sh ratelimiter opus
```

`runs/` is gitignored (working trees); graded evidence lands in `results/`.

## Results

See [results/RESULTS.md](results/RESULTS.md).
