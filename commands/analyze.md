---
description: Deconstruct an experiment codebase (any platform, any paradigm, any session count) into a strict PostgreSQL-feedable JSON spec via the Opus anatomist agent. Outputs experiment-spec.json + experiment-spec-summary.md in the current directory.
argument-hint: "[source-path-or-cwd] [SHORT_ID=...] [INTERVIEW=on|off]"
---

## /experiment-anatomy:analyze [source] [knobs]

Hand the experiment's code root (and, if separate, its docs path) to the
**anatomist** Opus agent. The agent runs the 12-pass workflow and emits
a strict JSON spec + a Korean summary.

### Arguments

- `<source>` — absolute path to the experiment's root directory. If
  omitted, the current working directory is used. May also be a GitHub
  URL or `owner/repo[#ref]` shorthand.
- `SHORT_ID=<slug>` — researcher's stable identifier (e.g. `TimeExp2`).
  Used as the upsert key in PostgreSQL. If omitted, the agent will ask
  during the interview pass.
- `INTERVIEW=off` — skip the interview pass; ship `open_questions[]`
  as the confirmation queue without asking anything.
- `RESEARCHER_INIT=<3-4 letters>` — lab initial that owns the analysis;
  ends up in `provenance.researcher_initial`. Defaults to whatever the
  caller's environment provides.
- `PARADIGM_GENRE=<genre>` — optional seed for `identity.paradigm_genre`.
- `DOCS=<extra-path>` — extra absolute path that contains README/MD/
  protocol files outside the source root (e.g.
  `/Volumes/.../Time2Dist/docs` when source is `.../Time2Dist/Exp2`).

### What the slash command does

1. Resolve `<source>` (single file → its parent; GitHub URL → shallow
   clone into a temp dir).
2. Resolve `DOCS=` if supplied; otherwise auto-look for `README*` /
   `docs/` near the source.
3. Hand-off to the `anatomist` agent with a single grounded message
   containing:
   - the file tree (depth ≤4, ≤300 entries)
   - the entry file's full contents (capped at 80KB)
   - up to ~5 supporting files (config/setup/saved-sink helpers)
   - the doc bundle (≤50KB total)
   - the knobs above
4. Agent runs Passes 1–12 and emits a JSON code block + Korean MD.
5. Slash command extracts the JSON (`from-first-{-to-last-}`) and writes:
   - `./experiment-spec.json` (validates against
     `schemas/experiment-spec.schema.json` — fails loudly if not)
   - `./experiment-spec-summary.md`
6. Prints the headline (reproducibility score / rigor score / open
   question count) and the path to both files.

### Examples

```bash
# Run against the current directory (cwd is the experiment root):
/experiment-anatomy:analyze

# Specific path + a separate docs directory:
/experiment-anatomy:analyze /Volumes/CSNL_new-1/people/JOP/Magnitude/Experiment/Time2Dist/Exp2 \
  DOCS=/Volumes/CSNL_new-1/people/JOP/Magnitude/Experiment/Time2Dist/docs \
  SHORT_ID=TimeExp2 \
  PARADIGM_GENRE=estimation \
  RESEARCHER_INIT=JOP

# From a public GitHub repo (no clone needed if the agent can fetch):
/experiment-anatomy:analyze https://github.com/some-lab/jspsych-decision INTERVIEW=off
```

### After analysis

The two output files are yours to inspect. To push them into PostgreSQL:

```bash
python3 <plugin>/scripts/upsert-to-postgres.py ./experiment-spec.json
```

Open questions you skipped (`INTERVIEW=off` or "그만") remain queued in
`spec_open_questions` for later confirmation.

### Notes

- The agent never edits your code or runs your experiment. Read-only.
- Local-only by default: code/docs/JSON never leave the machine the
  Claude Code session is running on. If you need a remote DB push,
  that is a separate explicit action (`upsert-to-postgres.py`).
- Hierarchy / factors / saved-variables structure is identical regardless
  of platform or session count — that's the whole point of the schema.
