# experiment-anatomy

> Opus-driven structured deconstruction of an experiment codebase.
> Same JSON shape regardless of platform, paradigm, or session count.
> Feeds directly into a lab PostgreSQL.

A Claude Code plugin that opens a session in which an **Opus anatomist**
reads a researcher's code + README and emits a strict, evidence-grounded
JSON spec describing the experiment's anatomy:

- Identity (title, paradigm genre, summary)
- Platform (framework, language, runtime, dependencies, version-pinning)
- Hierarchy (experiment → session → run/block → trial; phases per session)
- Manipulated variables (factors) — every one carries `role` (between-
  subject / within-subject / within-session / per-trial / derived)
- Conditions (realized combinations only — no Cartesian explosion;
  counterbalancing goes into a free-form design matrix summary)
- Parameters (setup constants — timing, screen, paths)
- Saved variables across 5 scales × 9 categories
- Display outputs (stimulus + experimenter figures)
- Storage paths
- Reproducibility (seed pinning, randomization scheme, version pinning,
  environment capture, deterministic paths) — 0–100 score with components
- Rigor (counterbalancing, sample-size justification, blinding,
  pre-registration, exclusion rules, static checks) — 0–100 score
- Open questions (everything the anatomist could not determine — queued
  for researcher confirmation)
- Provenance (model, plugin version, timestamp, files analyzed)

## Why?

A lab needs every experiment described in **one shape** so the database
can aggregate. The same researcher might have a PsychoPy script with no
sessions, a 5-day PTB study, and a jsPsych pilot — current tools produce
3 different documents. This plugin produces 1.

The anatomist runs a **map-first grounded interview** (mirroring the
csnl-archive plugin's methodology): when the code is unclear, it asks
one concrete multi-choice question at a time, with the code line as
evidence. The researcher's answers fold back into the spec.

## What's deployed where

- **Plugin** (this repo): the marketplace plugin you install with
  Claude Code; the agent definition + slash commands + prompt fragments.
- **Output JSON** (per analysis): one file in the researcher's cwd,
  shape-identical for every experiment.
- **PostgreSQL spec tables** (your lab DB): apply the DDL block in
  `schemas/postgres-mapping.md`. The `scripts/upsert-to-postgres.py`
  script transactionally lands the JSON into them.

## Install

```bash
# Add this repo as a Claude Code plugin marketplace, then install:
/plugin marketplace add CSNL-vnilab/experiment-anatomy
/plugin install experiment-anatomy@experiment-anatomy-marketplace
```

See [INSTALL.md](./INSTALL.md) for prerequisites + lab DB DDL.

## Use

In a fresh Claude Code session, `cd` into the experiment's code root
(or pass it as an argument):

```bash
/experiment-anatomy:analyze /path/to/experiment SHORT_ID=TimeExp2 PARADIGM_GENRE=estimation RESEARCHER_INIT=JOP
```

The anatomist runs 12 passes, asks at most 10 grounded questions when
ambiguity remains, and emits:

- `./experiment-spec.json` — strict JSON conforming to
  [`schemas/experiment-spec.schema.json`](./schemas/experiment-spec.schema.json)
- `./experiment-spec-summary.md` — 80-line Korean Markdown summary

To land the spec into PostgreSQL:

```bash
/experiment-anatomy:export ./experiment-spec.json
# or directly:
python3 scripts/upsert-to-postgres.py ./experiment-spec.json
```

## Slash commands

- `/experiment-anatomy:analyze [source] [knobs]` — deconstruct an experiment.
- `/experiment-anatomy:review <spec.json> [SOURCE=…]` — re-derive a spec
  after the researcher answered open questions.
- `/experiment-anatomy:export <spec.json> [DATABASE_URL=…]` — upsert into
  PostgreSQL via the reference script.

## Design notes

- **Local-only by default.** Code, docs, and output never leave the
  researcher's machine. PostgreSQL export is a separate, explicit step.
- **Same shape, every experiment.** Empty lists and `null`s where a
  paradigm legitimately has nothing. The schema's `additionalProperties:
  false` enforces it.
- **Evidence-grounded.** Every field with provenance has a `path:line`
  or `interview: <hash>` entry. The PostgreSQL row carries the evidence.
- **Researcher owns it.** When they push back ("그건 IV 아니야"), the
  anatomist edits and notes "interview: confirmed". The researcher is
  the verdict; the agent is the harness.

## Output schema overview

```
experiment-spec
├── schema_version
├── identity { title, short_id, summary, paradigm_genre, … }
├── platform { framework, language, dependencies[], score }
├── hierarchy { one_liner, sessions[]: { phases[] }, totals }
├── factors[] { name, type, role, levels, evidence[] }
├── conditions[] { label, factor_assignments, … }
├── parameters[] { name, value, shape, unit, evidence[] }
├── saved_variables[] { name, scale, category, format, sink, evidence[] }
├── display { stimulus_outputs[], figure_outputs[] }
├── storage { data_paths[], backup_paths[], naming_convention }
├── reproducibility { seed, randomization, version_pinning, … , score }
├── rigor { counterbalancing, sample_size, blinding, … , checks, score }
├── open_questions[] { topic, question, evidence, options[] }
└── provenance { plugin_version, schema_version, analyzed_at, model, … }
```

Full schema: [`schemas/experiment-spec.schema.json`](./schemas/experiment-spec.schema.json).
PostgreSQL DDL + upsert flow: [`schemas/postgres-mapping.md`](./schemas/postgres-mapping.md).

## Audience

**CSNL lab internal use.** The plugin's lenses encode CSNL conventions
(per-subject pre-generated schedules in `trial_schedule.mat`, the
`make_schedule_*.m` generator pattern, the per-block `par.tp.<channel>`
timing structure, …). Non-CSNL labs can fork and prune lab-specific
identifiers if useful.

## Changelog

### v0.1.1 (interview-driven hardening)

Based on a real-experiment correctness review:

- **PTB lens — "Pre-generated schedule" pattern as first-class**:
  detect via `load(*schedule*.mat)` AND a generator file
  `(make|generate|build|prep|seed)_?.*(schedule|trial).*\.m`. When
  active, enforce `factor.level_source="inline-literal"`,
  `randomization.scheme="fixed_schedule"`, FULL seed credit (gold-
  standard reproducibility).
- **Within-subject vs between-subject counterbalance**: classification
  follows what the generator iterates over (per `(subj, day)` →
  within; per `subj` only → between). Read the generator source —
  the schedule `.mat` only stores the resolved mapping, not the scheme.
- **Anatomist passes 3/4/5/10 updated** to detect the schedule pattern,
  pull the generator into the bundle, derive `design_matrix_summary`
  from generator source, and award seed/randomization full credit
  automatically when active.
- **Hard rule strengthened — "no invented counts"**: `n_blocks`,
  `n_trials_per_block`, `total_trials_estimate`, level values must be
  read from a literal in the source OR left null + queued in
  `open_questions[]`. Never filled from intuition or sibling
  experiments.
- **New static check `schedule_consistency`**: when the schedule
  pattern is active, literal block/trial constants must agree with
  schedule cell-array dimensions; mismatch flags + open_question.
- **Example corrected**: `examples/timeexp2-example.json` reflects the
  real TimeExp2 structure (within-subject counterbalanced dist,
  pre-generated schedule + scheduleRngState, illustrative-marker on
  counts). The earlier example had three factual errors that the
  hardening above is designed to prevent on future runs.

### v0.1.0

Initial release. See above sections for features.

## License

MIT. See [LICENSE](./LICENSE).

## Related

- `csnl-archive` — lab archive plugin that prompts the researcher
  through a similar map-first interview, but at the *project* level (not
  per-experiment). The anatomist borrows that plugin's interview
  methodology verbatim.
