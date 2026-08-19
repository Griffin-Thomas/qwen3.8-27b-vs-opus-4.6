# Results

Both models solved every task. All 14 held-out tests passed for both agents
across all 3 tasks, with no run ever seeing the graders, the task
definitions, or the other agent's work (verified by a transcript audit of
every tool call in all 6 runs; see `scripts/audit_isolation.py`).

The separation is wall-clock, not correctness.

| Task | Model | Holdout | Wall-clock | Turns | Source lines added | Test lines added | Output tokens |
|---|---|---|---:|---:|---:|---:|---:|
| ratelimiter | Qwen3.8-27B (xhigh) | 4/4 | 48m 33s | 16 | 3 | 42 | 35,917 |
| ratelimiter | Opus 4.6 (max) | 4/4 | 3m 48s | 8 | 3 | 47 | 9,384 |
| retry | Qwen3.8-27B (xhigh) | 6/6 | 6m 40s | 9 | 31 | 77 | 4,444 |
| retry | Opus 4.6 (max) | 6/6 | 54s | 8 | 22 | 80 | 2,488 |
| todo-cli | Qwen3.8-27B (xhigh) | 4/4 | 8m 07s | 18 | 8 | 25 | 4,850 |
| todo-cli | Opus 4.6 (max) | 4/4 | 43s | 11 | 5 | 33 | 2,292 |
| **Total** | **Qwen3.8-27B** | **14/14** | **63m 20s** | 43 | 42 | 144 | 45,211 |
| **Total** | **Opus 4.6** | **14/14** | **5m 25s** | 27 | 30 | 160 | 14,164 |

## Reading notes

- **Wall-clock ratio is 11.7x overall**, ranging from 7.4x (retry) to 12.8x
  (ratelimiter). The ratelimiter dominated Qwen's total: 35,917 output tokens
  of mostly extended reasoning at roughly 20 tok/s local decode.
- **Cost**: the local model's marginal cost is effectively zero (electricity).
  The 3 Opus runs total about $1.40 at first-party API rates.
- **Token-count asymmetry**: Opus's usage report shows ~200K cached input
  tokens per run; the local server's prefix cache is server-side and invisible
  to the client-side counters, so input-token columns are not comparable
  between models.
- **Both agents behaved like engineers, not test-gamers**: the transcript
  audit shows both models reproducing bugs empirically before fixing them,
  and neither touched anything outside its own working directory.

## Blinded qualitative review (OpenAI Codex)

Pass/fail can't rank 2 perfect scores, and this experiment was orchestrated
by Claude inside Claude Code, so having any Claude model judge the diffs
would invite self-preference bias (and having Qwen judge would invite the
mirror problem). The qualitative judging therefore went to a third model
family with no stake in the outcome: OpenAI Codex. It reviewed blind — per
task it saw the prompt, the baseline code, and the 2 diffs labelled Agent A
and Agent B with per-task randomized assignment; no timings, no token
counts, no model names. It ran against an isolated copy of the package
(`results/blind/`) with no filesystem path to the unblinding key, the run
directories, or the hidden graders. The verbatim verdict is in
[codex-verdict.md](codex-verdict.md); the mapping is in `blind-key.json`.

Unblinded, Codex picked the local model on all 3 tasks:

| Task | Codex's pick (blind) | Unblinded | Basis |
|---|---|---|---|
| ratelimiter | Agent B | **Qwen3.8-27B** | Qwen's regression tests genuinely pin both planted bugs; Opus's lockout-recovery test passes on the original buggy code |
| retry | Agent B | **Qwen3.8-27B** | Explicit retryable-status set `{429, 500, 502, 503, 504}` vs Opus retrying every 5xx including 501/505; stronger boundary and exhaustion tests |
| todo-cli | Agent A | **Qwen3.8-27B** | Functionally equivalent fixes; narrow win on import style and cleaner temp-file test scaffolding |

The sharpest finding was mechanically verified: running each agent's final
test suite against the original buggy limiter, Opus's suite fails only 1
test (the subsecond-truncation bug), so its recovery tests never pinned the
lockout bug; Qwen's suite fails exactly 1 test per planted bug. Codex also
noted real defects on Qwen's side (a docstring overstating the retry policy,
an unreachable `_MAX_DELAY` cap) and judged the todo-cli win "narrow" and
stylistic.

One cross-cutting criticism in the verdict was a harness artifact, not agent
behaviour: stray `__pycache__/*.pyc` files appeared in both agents' diffs
because the packaging step staged compilation artifacts from the agents' own
test runs and the grading step. It was symmetric across all 6 diffs and
Codex explicitly set it aside as non-distinguishing. The committed package is
kept byte-identical to what the reviewer saw.

## Bottom line

On these 3 small, realistic agentic tasks: functionally tied at 14/14; the
blinded third-party quality review went 3–0 to the local 27B model, mostly
on test rigour; and the frontier model was 11.7x faster end to end. n=3
tasks with 1 run per cell — treat this as a careful anecdote, not a
benchmark.
