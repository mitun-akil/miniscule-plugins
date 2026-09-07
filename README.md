# miniscule-plugins

A Claude Code plugin marketplace for small plugins that make Claude do less and
spend less. Add more plugins as subdirectories; one repo, one marketplace.

## Install

Add the marketplace, then install the plugin from it. Pick whichever source
applies:

```
# From GitHub
/plugin marketplace add mitun-akil/miniscule-plugins

# From a git URL (use this if the shorthand above cannot authenticate)
/plugin marketplace add https://github.com/mitun-akil/miniscule-plugins.git

# From a local clone or checkout
/plugin marketplace add ~/Documents/Projects/miniscule-plugins
```

Then, in all cases:

```
/plugin install pseudo-first@miniscule-plugins
```

> **This repository is private.** The GitHub sources above only work if your
> GitHub account has access to it and your local git credentials are configured.
> If you do not have access, ask the owner for a collaborator invite, or clone
> it yourself and use the local-path form.

Editing a plugin? Re-run `/plugin install` (or restart Claude Code) to pick the
changes up.

## Plugins

### `pseudo-first`

Splits a coding task between an expensive model that thinks and cheap models
that type.

1. **Plan** in plan mode. Ambiguity goes to you as questions, not guesses.
   Research goes to a caching subagent, not inline.
2. **Pseudocode only** - no comments, no prose, under 40 lines, every function
   signature named. Then `ExitPlanMode`.
3. **You approve.** Nothing is written before this.
4. **Fan out** - one Haiku subagent per file, all spawned in parallel, each with
   a self-contained prompt and no inherited context.
5. **Assemble** - the main model builds, tests, and fixes the seams.

Invoke explicitly with `/pseudo-first:go`, or let it trigger itself on coding
tasks. A `UserPromptSubmit` hook adds a one-line reminder to every prompt.

#### Knowledge cache

Research is written to disk so a deep dive happens once. The researcher reads
the cache before doing any work, and refreshes an entry when it is over 30 days
old or its cited paths have moved.

| Kind | Path | For |
|---|---|---|
| External | `~/.claude/knowledge/` | Library, API, protocol, framework facts. Not repo-specific. |
| Repo | `<project>/.claude/knowledge/` | How this codebase does something. Commit it and your teammates get it too. |

One topic per file, frontmatter plus terse bullets, `verified:` date, real
sources. Never secrets.

#### Coder permissions

Out of the box the coders get `Read, Write, Edit, Grep, Glob` and
`permissionMode: acceptEdits` - they edit files without prompting but **cannot
run shell commands**. To give them full control, uncomment the two lines in
`pseudo-first/agents/coder.md` and reinstall.

#### Known limitation

**Nothing can programmatically force a session into plan mode.** The skill and
the hook instruct plan-mode behaviour and gate all writes behind
`ExitPlanMode`, but if you want the gate to be truly unskippable, set plan mode
as your default in your own config.

`effort: low` on the coder is set on the assumption it reduces deliberation;
that is not documented, so the agent is *also* told in prose to implement
literally without redesigning. The prose is what does the work.

## Adding a plugin

Create `<name>/.claude-plugin/plugin.json` plus whatever `skills/`, `agents/`,
or `hooks/` it needs, then add an entry to `.claude-plugin/marketplace.json`
with `"source": "./<name>"`.
