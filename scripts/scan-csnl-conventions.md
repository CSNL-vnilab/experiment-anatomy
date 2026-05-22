# Harness — re-running the CSNL conventions survey

This is the reproducible recipe for the `db/csnl-conventions.json` +
`db/conventions-summary.md` survey. It can be re-run whenever a new
researcher initial joins the lab or an existing tree changes
substantially (e.g. a new project line).

## What the harness IS

A pattern, not a script. Each researcher's tree is explored by ONE
**isolated Explore subagent**: a sub-task launched in the same Claude
Code session that owns its own context window (does not see the
orchestrator's earlier conversation or other agents' code) and has
only read-only tools (Read / Grep / Glob / Bash for `ls`). The
orchestrator dispatches all subagents in a SINGLE message so they run
in parallel.

The "harness" is therefore:

1. A templated brief (below) — the same wording for every researcher,
   varying only by initial.
2. A fixed output schema (sections per agent) — same Markdown shape so
   the orchestrator can mechanically collate.
3. The orchestrator's collation step — read each agent's Markdown,
   transcribe into the JSON DB row + cross-researcher patterns.

A plain shell script can NOT dispatch isolated-context Claude
subagents; that's a Claude-Code-side capability. The harness must be
re-run from a Claude Code session that has Agent tool access.

## Prerequisites

- `/Volumes/CSNL_new-1/Memory/` mounted (or
  `/Volumes/CSNL_new/Memory/` — see the lab-reservation analyzer's
  mount auto-correction notes).
- Claude Code session with Agent tool and Explore subagent type.
- Stable network — each agent reads from the SMB-mounted volume.

## Step 1 — pre-flight: which initials exist?

In the Claude Code session, run:

```bash
ls /Volumes/CSNL_new-1/Memory/ | grep -v "^7T$\|^Eyelink$\|^Batch$\|^Grant$\|^Papers$\|^Reports$\|^Slack$\|^Workshop$\|^MetaData$\|^_lab_ai_harness$\|^Misc$\|^SfM$\|^회의록$"
```

(The exclusions are facility/equipment directories, not researchers.)

Cross-check against the active roster (the lab CLAUDE.md or
`csnl_meta_knowledge.md` lists current members). The 2026-05-22
roster: BYL, BHL, DG, JHR, HSL_MSY, JOP, JSL, KY, MSY, HJL — plus
BRL, CRC, CWLL, HG, HSL (single), JYA, JYK, LS, MJC, SK, SMJ, SYJ
which may or may not have current experiment code.

## Step 2 — dispatch parallel subagents

In a single Claude Code message, dispatch one Agent call per initial.
Use the **Explore** subagent type (read-only). The full brief
template:

```
Read-only survey. Root: /Volumes/CSNL_new-1/Memory/<INIT>/

Goal: find this researcher's EXPERIMENT-RUNNING code (stim
presentation + response capture in a trial loop) and characterize
their personal coding conventions. EXCLUDE analysis code (eye-
tracking post-processing, MRI/fMRI analysis, general data plotting,
QC scripts, statistical reporting).

How to distinguish experiment-run vs analysis:
- RUN code MUST contain: stimulus presentation calls
  (Psychtoolbox Screen('OpenWindow')/Screen('Draw…')/Screen('Flip'),
  PsychoPy visual.Window/win.flip()/<stim>.draw(),
  jsPsych initJsPsych/timeline, lab.js Sequence({content:[…]}),
  mgl mglOpen/mglFlush/mglBltTexture) AND a trial loop AND response
  capture (KbCheck/PsychHID/event.waitKeys/jsPsych.data/mglGetKeyEvent).
- ANALYSIS code (EXCLUDE) typically has: analyze_*/proc_*/plot_*/
  fig_*/extract_*/qc_* filenames; references to .nii, NIfTI, SPM,
  FSL, AFNI, fMRIPrep, BIDS, mrtools; references to eye-tracker
  post-processing (EyeLink .edf parsing without live experiment,
  gaze/fixation/saccade *analysis* libraries); pandas/numpy data
  manipulation without stim presentation; matplotlib/seaborn
  plotting scripts; statistical model fitting (lme4, statsmodels,
  brms).
- BACKUP / LEGACY dirs (EXCLUDE): *_backup_<date>/, archive/,
  Old_*/, legacy/, deprecated/, *.asv, *-legacy-browsers.js,
  subjData_old/, .svn-base, *_temp_experiment/ (when a non-temp
  sibling exists).
- BUILD-INFRA (EXCLUDE): setup.py / pyproject.toml / *.egg-info/ /
  setuptools/ dirs.

Walk the tree depth ≤6, file count cap ~500 (sample if larger).
Prefer mtime-recent + paths containing
experiment/exp/task/paradigm/stim/run/main.

For each candidate experiment dir (max 10), report:
- path (relative to <INIT>/)
- framework: psychtoolbox | psychopy | psychojs | jspsych | lab.js |
  mgl | opensesame | neurobs | custom | other | unknown
- entry file(s)
- schedule pattern: { active: yes/no/mixed, generator_file: <path or
  null>, schedule_mat: <path or null>, evidence: <file:line> }
- file naming convention (one sentence)
- distinctive features (3-5 bullets — what a downstream lens / harness
  needs to know)
- evidence (file:line refs for the above)

Also emit:
- excluded[] (max ~15): each entry { path, reason:
  eyelink-analysis | mri-analysis | generic-postproc | backup | legacy
  | build-infra | stimulus-prep | other, one-line justification }
- conventions_observed[]: 3-7 bullets — patterns specific to THIS
  researcher.
- open_questions[]: things that couldn't be answered from a read-only
  scan.

Output as a single Markdown block under header "## <INIT>" with the
sections above. Be terse. Quote real evidence. Do not modify files.
```

For each initial, substitute `<INIT>`. If the initial has known
project hints (e.g. JOP's pre-generated schedule pattern), append
ONE line of guidance — but never override the universal criteria.

## Step 3 — collation

Each subagent returns one Markdown block. The orchestrator transcribes
into `db/csnl-conventions.json`:

- `researchers.<INIT>.candidates[]` ← agent's candidate list (after
  removing any duplicate or analysis entries the agent included by
  mistake — read the report critically).
- `researchers.<INIT>.excluded[]` ← agent's excluded list.
- `researchers.<INIT>.conventions[]` ← agent's conventions_observed.
- `researchers.<INIT>.open_questions[]` ← agent's open_questions.

Then re-derive cross-researcher sections:

- `cross_researcher_patterns.framework_distribution` — group by
  framework.
- `cross_researcher_patterns.schedule_pattern_taxonomy` — group by
  schedule mechanism (pre-generated `.mat`, in-script rand, external
  xlsx, adaptive).
- `cross_researcher_patterns.entry_naming_conventions` — collect all
  observed entry-filename patterns.
- `cross_researcher_patterns.analysis_exclusion_signatures` — collect
  all observed analysis markers (paths / library imports / filenames).
- `cross_researcher_patterns.key_observations_for_lens_tuning` —
  bullets that should feed v0.2 lens improvements.

Write `db/conventions-summary.md` as the human-facing companion to the
JSON (headline counts + taxonomy + per-researcher one-line capsules).

## Step 4 — commit

```bash
cd <plugin-dir>
git add db/csnl-conventions.json db/conventions-summary.md
git commit -m "db: refresh CSNL conventions survey YYYY-MM-DD"
git push
```

## Cost notes

- ~3-8 min per subagent (varies by tree size + SMB read latency).
- 10 subagents in parallel → wall-clock ~5-10 min.
- One full survey costs roughly the price of a long Opus session.
- Re-run cadence: probably quarterly or on-demand when a major
  project line lands.

## What NOT to do

- Don't dispatch one giant agent over all initials at once — context
  pollution means later researchers get worse signal than earlier
  ones. The whole point of isolation is even quality per researcher.
- Don't try to drive this from a plain shell script — Claude's
  parallel isolated-context Agent dispatch is the load-bearing part.
- Don't merge HSL_MSY's report into HSL or MSY — joint workspaces are
  their own row.
- Don't ship the survey as the anatomist's input — it's *reference*
  for the orchestrator (the human/agent who tunes lenses + writes
  v0.2). The anatomist still analyzes one experiment at a time.

## Provenance

- Original harness run: 2026-05-22
- Orchestrator: Claude Opus 4.7 (1M context)
- 10 parallel Explore subagents
- Result: [`../db/csnl-conventions.json`](../db/csnl-conventions.json)
- Findings folded into v0.2 backlog at the bottom of
  [`../db/conventions-summary.md`](../db/conventions-summary.md).
