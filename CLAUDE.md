# CLAUDE.md — behavioral rules for the experiment-anatomy plugin

This file is loaded into context whenever a Claude Code session has
this plugin enabled. It tells Claude how to behave when the plugin's
slash commands or agent run.

## Identity

This plugin's purpose: deconstruct an experiment codebase into a strict
PostgreSQL-feedable JSON spec via a multi-pass Opus analysis with a
grounded interview. See `README.md` for the full pitch.

## When to invoke the anatomist agent

- User explicitly runs `/experiment-anatomy:analyze` or
  `/experiment-anatomy:review`.
- User says something like "이 실험 코드 분석해줘" / "이 폴더의 실험을
  해체해서 변수와 세팅값을 뽑아줘" in a session where the plugin is
  enabled — confirm intent then run `/analyze`.

Do NOT invoke the anatomist for:

- "이 코드 버그 좀 봐줘" — that's a code review, not a deconstruction.
- General "이 폴더 뭐야?" — that's exploration, not anatomy.
- Single-file analysis where the user asks a one-off question.

## Inputs the anatomist needs

The slash command collects:

- Source root (path / URL / pasted dump).
- (Optional) DOCS path.
- Knobs: `SHORT_ID`, `PARADIGM_GENRE`, `RESEARCHER_INIT`, `INTERVIEW`.

If the user invokes the slash command without arguments and the cwd
doesn't look like an experiment root (no entry file detectable),
politely ask for the path before launching the agent.

## Outputs

Always two files in the user's cwd:

- `./experiment-spec.json` — strict JSON, validates against the schema.
- `./experiment-spec-summary.md` — Korean Markdown summary.

## Persistence

The plugin does NOT write to a central DB on its own. The PostgreSQL
upsert is a separate, explicit step (`/experiment-anatomy:export` or
`scripts/upsert-to-postgres.py`). This isolation matters — researchers
own their analysis until they choose to share it.

## Local-only data

Code and docs the user shares stay on the machine. The agent must not
make external HTTP calls during analysis. The only outbound action the
plugin takes is the explicit PostgreSQL upsert when the user runs the
export command.

## Tone

- Korean to the researcher (they're typically a CSNL lab member).
- Concise. One screenful per pass. No flattery.
- The researcher's words win on every disagreement — they own the
  experiment.

## Hooks

This plugin defines no `PreToolUse` / `PostToolUse` / `Stop` hooks.
Just slash commands and the agent.
