# Measuring whether pseudo-first actually saves anything

## Measure cost, not tokens

The plugin moves typing from an expensive model to a cheap one. A run can use
*more* total tokens and still cost much less. Counting tokens will mislead you.

Count tokens **per model**, then apply per-model prices. `tokencount.py` does
the first part.

## Count subagents or the result is fake

Subagent usage is **not** written to the main session transcript. It lives in:

```
~/.claude/projects/<slug>/<session-id>/subagents/agent-*.jsonl
```

Counting only the main transcript undercounts precisely the arm that offloads
to Haiku, which manufactures a win that is not there. `tokencount.py` sums both.

## Pick the right task

- **2-4 files of real work.** The plugin explicitly skips one-liners, and
  fan-out has fixed per-agent overhead: each subagent re-sends a system prompt.
  On a tiny task, three Haiku agents cost *more* than just writing it.
- Something you can objectively check - it builds, tests pass.
- Not something you have already solved in another session this week.

## Protocol

Both arms must start from an identical repo state and a **fresh session**.
Context and prompt cache carry over between turns, so reusing a session
contaminates everything.

```bash
# Snapshot the starting point once
git checkout -b bench-base && git commit -am "bench start" || true

# --- Arm A: baseline (plugin disabled) ---
# /plugin uninstall pseudo-first@miniscule-plugins   (or /plugin disable)
git checkout bench-base && git checkout -B run-a
claude          # fresh session; paste the task prompt verbatim; let it finish
# note the session id:
python3 tools/tokencount.py --list | head -1

# --- Arm B: pseudo-first ---
# /plugin install pseudo-first@miniscule-plugins
git checkout bench-base && git checkout -B run-b
claude          # fresh session; paste the SAME prompt verbatim
python3 tools/tokencount.py --list | head -1
```

Then:

```bash
python3 tools/tokencount.py <session-a> --prices tools/prices.json
python3 tools/tokencount.py <session-b> --prices tools/prices.json
```

**Alternate arms and do 3 reps each (A,B,A,B,A,B).** Run-to-run variance on the
same prompt is large - a single pair of runs tells you almost nothing. If the
two arms differ by less than ~20%, treat it as noise.

## Record quality too, in the same table

A cheap run that ships broken code saved nothing. For every run log:

| Run | Arm | Cost | Built? | Tests pass? | Human correction turns | Wall clock |
|-----|-----|------|--------|-------------|------------------------|------------|

"Human correction turns" is the one people forget and it is often decisive: if
the Haiku arm needs three rounds of you fixing its output, the second and third
rounds are cost too, and they land on the expensive model.

## Confounders to keep honest about

- **Cache reads dominate.** They are typically the large majority of billable
  tokens and are priced far below fresh input. Keep both arms similar in length
  and turn count, and always read the per-model breakdown rather than one total.
- **The hook taxes every prompt** in the plugin arm, including non-coding turns.
- **The approval gate adds round trips**, each re-reading the context.
- **Order effects:** you get better at the task. Paste an identical prompt every
  time and alternate arms.
- **Model routing:** confirm which model each arm's main session actually used.
  Comparing an Opus baseline against a Sonnet plugin run measures the model, not
  the plugin.

## Cheaper sanity check

If you do not want the full protocol, run `/cost` at the end of each arm. Less
precise and it may or may not include subagents - verify it against
`tokencount.py` on one run before trusting it.
