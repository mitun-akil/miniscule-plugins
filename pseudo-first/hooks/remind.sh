#!/usr/bin/env bash
# Injects one line on every prompt. Kept to one line on purpose: it fires on
# non-coding chatter too, so it must be near-free in tokens.
printf '%s' '{"hookSpecificOutput":{"hookEventName":"UserPromptSubmit","additionalContext":"If this turn writes or changes code, use the pseudo-first skill: plan mode, confirm assumptions, tiny commentless pseudocode, ExitPlanMode for approval, then parallel coder subagents. Skip it for one-liners and questions."}}'
