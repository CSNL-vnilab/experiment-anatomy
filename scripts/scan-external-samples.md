# Harness — re-running the external psychophysics meta-search

Companion to [`scan-csnl-conventions.md`](./scan-csnl-conventions.md).
The internal harness surveys CSNL `/Volumes/CSNL_new-1/Memory/<INIT>/`
trees with isolated **Explore** subagents (read-only filesystem).
THIS external harness surveys public **GitHub orgs + OSF deposits + lab
websites** with isolated **general-purpose** subagents (read-only on
the local FS, write-only to `/tmp/`, plus WebSearch/WebFetch).

Re-run quarterly or whenever a new prominent psychophysics lab releases
substantial open-source code.

## What the harness IS

A **pattern**, not a script. Each lab roster is explored by ONE
**isolated general-purpose subagent**: a sub-task with its own context
window, full toolset minus permission to edit anything outside `/tmp/`.
The orchestrator dispatches all subagents in a SINGLE message so they
run in parallel.

## Prerequisites

- Network access (the agents WebSearch + WebFetch + `git clone`).
- Disk space for shallow clones under `/tmp/` (~200-500 MB per lab).
- Claude Code session with Agent tool, `general-purpose` subagent type,
  WebSearch+WebFetch tools, Bash with sandbox permissions to write
  `/tmp/`.

## Step 1 — pre-flight: lab roster

Pick 3-6 labs depth-first over breadth. First run targeted:

- **Gardner Lab** (Stanford) — author of `mgl`; canonical mgl reference
- **Acerbi Lab** (Helsinki) — Bayesian adaptive (`psybayes`) + post-hoc
  inference (BADS, VBMC)
- **Stocker Lab** (UPenn) — Bayesian observer models in orientation /
  speed / time perception
- **Sims Lab** (RPI / AdaCog) — rate-distortion theory in perception +
  memory
- **Adjacent labs** — Brainard, Wichmann, Wei Ji Ma, Gold, Pelli,
  Wandell, Heeger (pick 3+ of these for the "Adjacent" bucket)

The roster comes from the user's brief or from a paper-citation
expansion via Google Scholar.

## Step 2 — dispatch parallel subagents

In a single Claude Code message, dispatch one `general-purpose` Agent
call per lab roster. Use `model: opus`. Brief template (per agent):

```
Mission: external psychophysics code meta-search. Find <LAB>'s public
experimental code on GitHub + OSF + lab website. Catalogue rigorously
for the `experiment-anatomy` plugin's sample DB.

Use WebSearch, WebFetch, Bash (git clone into /tmp/). Write only to
/tmp/. Do NOT Edit/Write outside /tmp/.

Search & fetch:
1. WebSearch for the lab's GitHub org or user handle.
2. List public repos grouped as { framework | analysis | experiment |
   utility | other }.
3. For ≥3 experiment-running repos, clone shallow into /tmp/<lab>-<repo>/
   (--depth=1) and read entry files + README.
4. Probe OSF (site:osf.io <PI>) for paper-companion code+data
   deposits.
5. Probe the lab site for downloadable code/data zips.

For each experiment-running sample, capture:
- name, source URL, license, last activity year
- framework (mgl | psychtoolbox | psychopy | psychojs-builder |
  psychojs-handwritten | jspsych | lab.js | custom | external | other)
- entry file(s)
- paradigm genre + hierarchy one-liner
- factors[] with {name, levels, role}
- parameters[] with {name, value, shape}
- schedule_mechanism
- adaptive procedure (family + rule + per-trial-state-saved)
- saved variables (path + shape)
- 3-5 distinctive conventions
- evidence file:line refs

Also:
- Repo inventory (every public repo with one-line classification)
- Cross-comparison with CSNL where applicable
- Recommended lens-rule highlights (3-7 bullets)
- Pitfalls (3-5 bullets)
- Skipped queries / reasons

Output as a single Markdown block under "## <LAB>" with the sections
above. Be terse. Quote real evidence. Never invent. Skipped → note
the reason briefly.
```

Tailor the "Specialty:" hint per lab (Gardner = "mgl is your canonical
reference"; Acerbi = "BADS/VBMC are inference tools, psybayes is
adaptive engine"; Stocker = "expect data+model only, stimulus code
probably absent"; etc.). Don't override the universal criteria.

## Step 3 — collation

Each subagent returns one Markdown block. The orchestrator transcribes
into `db/external-samples.json`:

- `labs.<lab>.samples[]` ← agent's per-sample structured blocks.
- `labs.<lab>.release_shape` ← summarized from agent's findings.
- `reference_frameworks[]` ← framework-only repos (mgl, snow-dots,
  BrainardLabToolbox, etc.) the agent identified.

Then derive `cross_lab_findings`:

- `framework_distribution_external` — group samples by framework field.
- `schedule_pattern_distribution` — group by schedule_mechanism.
- `counterbalancing_styles` — read CB scheme from each sample.
- `adaptive_procedure_distribution` — group by adaptive.family.
- `saved_data_conventions` — read saved_variables shapes.
- `cross_run_state_patterns` — flag `getLastStimfile` / cross-session
  posterior persistence.
- `release_shape_taxonomy` — group by experiment+analysis vs.
  data+model vs. frontend-not-released vs. framework-only.
- `key_observations_for_lens_tuning` — bullets that should feed v0.2+
  lens improvements.

Write `db/external-samples-summary.md` as the human-facing companion.

## Step 4 — commit

```bash
cd <plugin-dir>
ALLOW_FEATURE_BRANCH=1 git add db/external-samples.json db/external-samples-summary.md scripts/scan-external-samples.md
ALLOW_FEATURE_BRANCH=1 git commit -m "db: external psychophysics samples survey YYYY-MM-DD"
ALLOW_FEATURE_BRANCH=1 git push
```

(The plugin repo's branch-guard hook may require the `ALLOW_FEATURE_BRANCH=1`
prefix if `CLAUDE_PROJECT_DIR` points at a sister repo with a
non-main branch.)

## Cost notes

- ~5-12 min per subagent (web latency + shallow clones + light reads).
- 5 subagents in parallel → wall-clock ~8-12 min.
- One full external survey ≈ price of a long Opus session.
- Re-run cadence: quarterly, or when new labs publish substantial
  open-source experiment code, or after a major lens overhaul.

## What NOT to do

- **Don't dispatch one giant agent across all labs at once** — context
  pollution. Even quality per lab is the point of isolation.
- **Don't classify framework-only repos as experiment samples** (mgl,
  BrainardLabToolbox, snow-dots, psychopy-pixx) — list them in
  `reference_frameworks[]` instead.
- **Don't dismiss data+model packages as "incomplete experiments"** —
  Stocker / Acerbi paper companions ARE a valid release shape (
  `paper_companion_only`). Treat them as documenting trial design
  implicitly, not as failed releases.
- **Don't double-count borrowed datasets** — Stocker Speed_Prior 2022
  re-releases Stocker & Simoncelli 2006's data. One repo per dataset,
  not per paper.
- **Don't conflate homonyms** — Princeton economist Christopher A.
  Sims (csolve, gensys, csminwel) ≠ RPI cognitive scientist Chris R.
  Sims. Always confirm the GitHub handle's institutional affiliation
  before attributing.

## Provenance

- Original harness run: 2026-05-22
- Orchestrator: Claude Opus 4.7 (1M context)
- 5 parallel `general-purpose` Opus subagents (one per lab roster)
- Result: [`../db/external-samples.json`](../db/external-samples.json)
- Companion: [`../db/external-samples-summary.md`](../db/external-samples-summary.md)
