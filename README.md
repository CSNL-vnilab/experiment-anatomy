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

### v0.2.0 (mgl + PsychoJS Builder + adaptive procedures + external-host)

Two parallel Opus agent harnesses (5 deep-uncertainty + 5 external
meta-search) produced 33 catalogued samples from Gardner / Acerbi /
Stocker / Sims / Brainard / Wichmann / Wei Ji Ma / Gold / Pelli /
Wandell. Folded into v0.2 lens improvements:

- **New `mgl` lens** (`prompts/lenses/mgl.md`) — Justin Gardner's
  MATLAB OpenGL framework. Two-mode classifier (`mgl-callback` for
  the canonical Gardner pattern vs `mgl-primitive` for HJL Main_RingExp).
  Encodes the callback architecture (no explicit `for iT` loop —
  `while … updateTask … tickScreen … end`), `task.parameter` /
  `task.randVars.uniform` / `task.randVars.calculated` factor roles
  (the third is a RESPONSE SLOT, not a factor — common LLM
  mistake), segment timing model with `synchToVol` for fMRI, eye-
  tracker variants (EyeLink / ASL / 9-pt manual). Cross-run warm-
  start via `getLastStimfile` flagged as reproducibility-affecting.
  Adaptive subsection: `upDownStaircase(nup,ndown,init,step,rule)`
  with Levitt vs PEST disambiguation, `multipleStaircase`
  interleaved-N-staircase pattern, threshold reporting via
  `computeThreshold(meanOfLastK reversals)`. Canonical-entry picker
  excludes `taskTemplate*.m` (framework, not entries), `*~`,
  `*.svn-base`, conflicted-copy siblings, prefers latest-dated
  `_YYMMDD.m`.
- **PsychoJS Builder export subsection** (`prompts/lenses/psychopy.md`
  § 5) — auto-generated 4 000-8 000-line web runtime. Four-file
  fingerprint (`.psyexp` + `.js` + `<name>-legacy-browsers.js` +
  `index.html` with `[PsychoPy]` title). Scheduler / flowScheduler /
  loopScheduler abstraction documented. Routine triple
  (`<r>RoutineBegin`/`EachFrame`/`End`) grouped as one node. **xlsx
  factor extraction rules**: column nunique → factor type
  (`nunique==1` → parameter; `≤8` → categorical; `≥10` even-spaced →
  continuous; `==row_count` string-like → stimulus catalog;
  sparse-fill → metadata). **Config-as-conditions trick**: 1-row
  xlsx with all-nunique==1 columns is a parameter sidecar, NOT a
  6-factor × 1-level design. Hand-written shuffle detection
  (`TrialHandler.importConditions` outside any
  `new TrialHandler({})`). Prolific / Pavlovia integration patterns.
  Auto-component telemetry vs researcher-added columns separated
  in `saved_variables[]` (Builder emits `<r>.started`, `<r>.stopped`,
  `<comp>.response`, `.rt`, `.duration` unconditionally —
  inflating these into `category=response` would over-count).
- **Adaptive-procedure subsection** in PTB lens — staircase
  (Levitt / PEST / Garcia-Perez), Quest (Watson 1983) / QUEST+
  (Watson 2017 `qpInitialize`), PSI (Kontsevich-Tyler via Acerbi's
  `psybayes`), Bayesian-adaptive (PF + info-gain like DG BAM).
  Each emits `adaptive_procedure` with family + update-rule
  verbatim + per-trial-state-saved + termination. Reproducibility
  award rules per family: replay requires response/strength arrays
  (staircase), intensity/response (Quest), full posterior history
  or per-trial particle cloud (Bayesian). Detection pitfall:
  `method='random'` TrialHandler with adaptive-LOOKING variable
  names is NOT adaptive; the discriminating test is "does the level
  for trial N depend on response on trial N-1 inside the same trial
  loop body?".
- **External-host pattern** in PTB lens — recognizes data-only
  workspaces where the runner is hosted on Pavlovia / OSF / a
  paper-companion GitHub. `platform.framework = "external"`
  sentinel; deconstruction proceeds from saved data columns +
  paper Methods rather than from a local runner.
- **Anatomist Pass 2** updated — framework enum now lists `mgl`
  (callback / primitive sub-variants), `psychojs-builder` /
  `psychojs-handwritten`, `external`. `platform.detection_confidence`
  thresholds documented (≥4 hard signals → ≥0.9; 2-3 → 0.7-0.9;
  ambiguous → open_question even with best guess).
- **Factors-live-in-multiple-places rule** in anatomist Pass 4 —
  per-framework checklist (PTB: literal / schedule.mat /
  randperm-runtime; mgl: parameter / randVars / expBlock.*Seq;
  PsychoPy/PsychoJS: xlsx columns / hand-written importConditions;
  jsPsych: factorial_design / randomization.factorial). Missing
  the schedule generator / xlsx / mseq source is the #1 way to
  undercount factors by 50-80 %.
- **New `db/external-samples.json`** + `db/external-samples-summary.md`
  + `scripts/scan-external-samples.md` — the meta-search results
  + reproducible re-run recipe. Both files carry full `_meta.provenance`
  / `Provenance` blocks naming the orchestrator model, the 5 agent IDs,
  the cloned `/tmp/` trees, the canonical upstream URLs, and tool-call
  counts per agent.
- **Schema 1.0.0 → 1.1.0** (additive, backward compatible):
  - `platform.framework` enum extended with `mgl`, `psychojs`,
    `psychojs-builder`, `psychojs-handwritten`, `external`.
  - New `platform.variant` (free-form sub-mode — `mgl-callback` /
    `mgl-primitive` / `mgl-hybrid` / `snow-dots` / `BrainardLabToolbox`).
  - New `platform.runtimes[]` for dual-export projects
    (`.psyexp + .py + .js` ships both `python-desktop` and
    `javascript-web`).
  - New `platform.external_host { kind, url, evidence }` for
    `framework="external"` workspaces.
  - New root `adaptive_procedure` object (family / engine /
    update_rule / rule_confidence / n_interleaved / interleaving_key /
    termination / per_trial_state_saved / warm_start / evidence).
- **Codex adversarial review pass** (run after v0.2 design freeze)
  caught 7 CRITICAL + 5 MEDIUM design issues. All 7 critical resolved
  before this commit:
  1. Schema enum drift (lens promised values schema didn't list) —
     fixed by 1.1.0 enum extensions above.
  2. mgl two-mode detector mis-handled the HJL/Main_RingExp case
     (primitive entry + framework files in same dir) — added explicit
     **`mgl-hybrid` mode** with call-graph-aware disambiguation.
  3. PsychoJS Builder four-file fingerprint was necessary-but-not-
     sufficient — added **Scheduler-graph hard-signal requirement**
     (≥3 of `flowScheduler.add(...)` cascade, RoutineBegin boilerplate,
     `nextEntry(snapshot)` advance pattern, started/stopped auto-
     telemetry pairs). Hand-written PsychoJS with the four files
     present now classifies as `psychojs-handwritten` instead.
  4. Missing root `adaptive_procedure` block — added to schema.
  5. Missing `platform.runtimes[]` — added.
  6. Missing `platform.external_host` — added.
  7. Unresolved adaptive rule (e.g. `cfg.rule` from absent config)
     conflicted with Hard Rule 2 ("no invention") — added explicit
     **fallback**: `update_rule=null`, `rule_confidence="low"`,
     open_question topic=`factors`.

  Medium issues resolved this commit:
  - **Lens loading mechanism** spelled out as a Read-tool action,
    not aspirational ("Read `${CLAUDE_PLUGIN_ROOT}/prompts/lenses/<x>.md`
    verbatim into context BEFORE running Passes 3-7").
  - **Adaptive reproducibility auto-credit** Pre-step added to Pass 10
    (parallel to SCHEDULE_ACTIVE auto-credit) — full randomization
    score when adaptive `per_trial_state_saved` is non-empty.
  - **External-host false-positive** prevention — detection now
    requires BOTH negative absence AND positive evidence (a
    documented Pavlovia / Gorilla / OSF / GitHub URL in README).
  - **`external-samples.json` key normalization** — renamed
    `factors_inferred_from_data_header` → `factors` (with `source`
    field), `hierarchy_data_tree` → `hierarchy_one_liner`,
    `release_shape` → `release_shape_note` consistently.

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

## CSNL conventions survey (`db/`)

A parallel-subagent **harness** that surveys every CSNL researcher's
`Memory/<initial>/` tree, distinguishes experiment-running code from
analysis (eye-tracker post-proc, fMRI analysis, plotting, stats),
and aggregates the lab's diverse coding conventions into a single
DB. Used as input when tuning lenses for v0.2.

- [`db/csnl-conventions.json`](./db/csnl-conventions.json) — full
  per-researcher rows + cross-researcher patterns.
- [`db/conventions-summary.md`](./db/conventions-summary.md) — human-
  facing summary (headline counts, schedule-mechanism taxonomy,
  per-researcher capsules, v0.2 backlog).
- [`scripts/scan-csnl-conventions.md`](./scripts/scan-csnl-conventions.md) —
  reproducible recipe for re-running the survey when the roster or
  projects change.

First run (2026-05-22): 10 researchers (BYL, BHL, DG, JHR, HSL_MSY,
JOP, JSL, KY, MSY, HJL), 10 parallel isolated Explore subagents,
~5-10 min wall-clock. Findings include: JOP is the only researcher
with the `make_*schedule*.m` + `trial_schedule.mat` +
`scheduleRngState` pattern (validates v0.1.1's detect-then-strict
policy); HJL uses `mgl` not PTB (v0.2 candidate for a new lens);
MSY is 100% PsychoJS Builder export; HSL_MSY is data-only with the
upstream task hosted externally.

## License

MIT. See [LICENSE](./LICENSE).

## Related

- `csnl-archive` — lab archive plugin that prompts the researcher
  through a similar map-first interview, but at the *project* level (not
  per-experiment). The anatomist borrows that plugin's interview
  methodology verbatim.
