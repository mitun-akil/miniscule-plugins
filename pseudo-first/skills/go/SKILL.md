---
name: pseudo-first
description: Use for ANY task that will write or change code - features, refactors, bug fixes, scripts, new files. Plans in plan mode, confirms assumptions, emits only tiny commentless pseudocode for approval, then fans out parallel Haiku subagents to write the real code. Also use when the user says "pseudo first", "plan then fan out", "cheap mode", or asks to minimise token spend on a coding task.
allowed-tools: Read, Grep, Glob, Agent, Task, AskUserQuestion, ExitPlanMode, Bash
---

# Pseudo First

Three phases. Do not blur them. Do not start Phase 2 before the human approves.

The expensive model plans. The cheap models type. Your job in Phase 1 is to make
the pseudocode so unambiguous that a Haiku agent with zero context can implement
it without asking anything.

## Phase 1 - Plan

Work in plan mode. If plan mode is not active, say so in one line and behave as
if it were: no edits until approval.

**Understand first.** Read the files the change actually touches and trace the
real flow. Laziness shortens the solution, never the reading.

**Confirm everything.** Any ambiguity that changes what gets built - target
files, naming, scope, edge-case handling, which of two approaches - goes to
`AskUserQuestion`. Batch questions into one call. Do not guess and do not
silently pick a default on anything the human would care about.

**Research only through the cache.** If the task needs external facts (a library
API, a protocol, a framework convention) or a deep dive into an unfamiliar part
of the codebase, do not research inline. Spawn the `doc-researcher` agent, which
checks the on-disk knowledge cache before doing any work. Pick its model to
match the question:

| Question | Model |
|---|---|
| Look up a documented API, config key, or signature | `haiku` |
| Synthesise docs, compare approaches, map a subsystem | `sonnet` (default) |
| Genuinely hard architecture or subtle semantics | `opus` |

Spawn independent research in parallel in a single message.

**Then emit pseudocode. Only pseudocode.** Hard rules:

- No comments. None.
- No prose before or after it. No design notes, no alternatives, no rationale.
- Group lines under `path/to/file.ext` headers, in the order they get built.
- One line per step. Plain imperative phrases, not real syntax.
- Name every function signature explicitly, with params and return - the coders
  wire against these and cannot see each other's work.
- Mark each file `[new]` or `[edit]`.
- Under 40 lines total. If it will not fit, the task is too big: say so and
  propose a split rather than writing 80 lines.

Shape:

```
pkg/parse/csv.go [new]
  ParseRows(path string) ([]Row, error)
    open file, defer close
    read header, map column name -> index
    per line: build Row, skip if malformed
    return rows

cmd/main.go [edit]
  main()
    flag: -in path
    call ParseRows
    on error: print to stderr, exit 1
    print rows as aligned table
```

Then call `ExitPlanMode`. Nothing else. Do not ask "does this look right" in
prose - `ExitPlanMode` is the approval gate.

## Phase 2 - Fan out

Only after the human approves.

Split the pseudocode into units, normally one per file. Then spawn every
independent unit **in a single message with multiple Task calls** so they run
concurrently, each with `subagent_type: coder`.

Each coder prompt must stand alone - the agent inherits no context and cannot
see the plan, the conversation, or its siblings. Include, every time:

1. The exact absolute file path, and whether it is new or an edit.
2. That unit's pseudocode slice, verbatim.
3. Signatures it must expose, exactly as written in the plan.
4. Signatures it may call from other units, with the note that those files may
   not exist yet - code against the signature, do not go looking.
5. Language, and any convention it must match (error style, logging, naming).
6. `Do not read files other than the ones named here. Do not add abstractions,
   comments, config, or tests that were not asked for.`

Sequence units only where one genuinely needs another's real output. Shared
types are not a dependency - put the type in the prompt of everyone who needs it.

## Phase 3 - Assemble

You do this, not Haiku. Cheap models write units; the expensive one owns the seams.

- Build, vet/lint, and run the tests. State the actual command and result.
- Fix wiring failures yourself. Do not re-spawn a coder for a two-line seam.
- If a unit came back wrong, re-spawn that one coder with a sharper prompt.
- Non-trivial logic leaves one runnable check behind - a small test or an
  assert-based self-check. Trivial one-liners need none.

Report: what was built, where, what command you ran to verify, and its result.
If something failed, say so with the output. Never claim verified work you did
not run.

## When to skip this workflow

One-line fixes, typos, renames, answering a question, reading code. The
three-phase dance costs more than it saves below roughly two files of work. Say
"too small for pseudo-first" and just do it.
