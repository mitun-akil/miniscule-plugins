#!/usr/bin/env python3
"""Per-model token accounting for a Claude Code session, subagents included.

Main session transcript:  ~/.claude/projects/<slug>/<session-id>.jsonl
Subagent transcripts:     ~/.claude/projects/<slug>/<session-id>/subagents/agent-*.jsonl

Subagent usage is NOT in the main transcript, so counting only the main file
undercounts any workflow that offloads to subagents. Both are summed here.

Usage:
  tokencount.py <session-id-or-transcript-path> [--prices prices.json]
  tokencount.py --list
"""
import collections, glob, json, os, sys

PROJECTS = os.path.expanduser("~/.claude/projects")
FIELDS = ("input_tokens", "cache_creation_input_tokens",
          "cache_read_input_tokens", "output_tokens")


def transcripts(session):
    """Main transcript + every subagent transcript for a session."""
    if session.endswith(".jsonl") and os.path.exists(session):
        main = session
    else:
        hits = glob.glob(f"{PROJECTS}/*/{session}.jsonl")
        if not hits:
            sys.exit(f"no transcript found for session {session!r} (try --list)")
        main = hits[0]
    subdir = main[:-len(".jsonl")]
    return [main] + sorted(glob.glob(f"{subdir}/subagents/agent-*.jsonl"))


def tally(paths):
    per_model = collections.defaultdict(collections.Counter)
    for p in paths:
        agent = "main" if not os.path.basename(os.path.dirname(p)) == "subagents" else "subagent"
        with open(p, errors="replace") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                msg = rec.get("message") or {}
                usage = msg.get("usage")
                if not usage:
                    continue
                c = per_model[(agent, msg.get("model", "?"))]
                for f in FIELDS:
                    c[f] += usage.get(f) or 0
                c["thinking_tokens"] += (usage.get("output_tokens_details") or {}).get("thinking_tokens") or 0
                c["messages"] += 1
    return per_model


def main():
    argv = sys.argv[1:]
    if not argv or argv[0] == "--list":
        rows = []
        for f in glob.glob(f"{PROJECTS}/*/*.jsonl"):
            rows.append((os.path.getmtime(f), os.path.basename(f)[:-6],
                         os.path.basename(os.path.dirname(f))))
        for _, sid, proj in sorted(rows, reverse=True)[:15]:
            print(f"{sid}  {proj}")
        return

    prices = {}
    if "--prices" in argv:
        prices = json.load(open(argv[argv.index("--prices") + 1]))

    paths = transcripts(argv[0])
    per_model = tally(paths)
    print(f"{len(paths)} transcript(s): 1 main + {len(paths)-1} subagent\n")

    hdr = f"{'where':9} {'model':30} {'msgs':>5} {'in':>9} {'cache_wr':>10} {'cache_rd':>10} {'out':>9} {'think':>8}"
    print(hdr); print("-" * len(hdr))
    grand = collections.Counter(); cost = 0.0; priced = True
    for (agent, model), c in sorted(per_model.items(), key=lambda kv: -kv[1]["output_tokens"]):
        print(f"{agent:9} {model:30} {c['messages']:5} {c['input_tokens']:9,} "
              f"{c['cache_creation_input_tokens']:10,} {c['cache_read_input_tokens']:10,} "
              f"{c['output_tokens']:9,} {c['thinking_tokens']:8,}")
        for k, v in c.items():
            grand[k] += v
        p = prices.get(model)
        if p and all(p.get(k) is not None for k in ("input", "output")):
            cost += (c["input_tokens"] * p["input"]
                     + c["cache_creation_input_tokens"] * p.get("cache_write", p["input"])
                     + c["cache_read_input_tokens"] * p.get("cache_read", p["input"])
                     + c["output_tokens"] * p["output"]) / 1e6
        else:
            priced = False

    print("-" * len(hdr))
    print(f"{'TOTAL':9} {'':30} {grand['messages']:5} {grand['input_tokens']:9,} "
          f"{grand['cache_creation_input_tokens']:10,} {grand['cache_read_input_tokens']:10,} "
          f"{grand['output_tokens']:9,} {grand['thinking_tokens']:8,}")
    billable = sum(grand[f] for f in FIELDS)
    print(f"\nbillable tokens (in + cache_wr + cache_rd + out): {billable:,}")
    if prices:
        print(f"cost: ${cost:.4f}" + ("" if priced else "  (INCOMPLETE - some models missing from price table)"))
    else:
        print("no --prices given; token counts only. Cost is the metric that matters:\n"
              "a Haiku token and an Opus token are not comparable.")


if __name__ == "__main__":
    main()
