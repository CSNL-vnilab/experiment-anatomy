# CSNL code-conventions survey — cross-researcher summary

Scanned 2026-05-22 from `/Volumes/CSNL_new-1/Memory/`. Ten researcher
initials (BYL, BHL, DG, JHR, HSL_MSY, JOP, JSL, KY, MSY, HJL) explored
by ten isolated Explore subagents in parallel (single Claude Code
dispatch). Read-only across the volume; no files modified.

Full per-researcher row data: [`csnl-conventions.json`](./csnl-conventions.json).
Harness reproduction guide: [`../scripts/scan-csnl-conventions.md`](../scripts/scan-csnl-conventions.md).

---

## Headline counts

| | researchers |
|---|---|
| **with experiment-run code on volume** | 9 (all except HSL_MSY) |
| **PTB MATLAB** | BYL, BHL, DG, JHR, JOP, JSL, KY |
| **mgl MATLAB** | HJL (only one) |
| **PsychoPy / PsychoJS** | BYL (online), MSY (entire workspace) |
| **lab.js / jsPsych raw** | none on volume; HSL_MSY task is hosted externally |
| **uses EyeLink/ASL** | BYL, JHR, JOP, JSL, KY, DG, HJL — i.e. everyone with MATLAB on lab hardware |
| **uses pre-generated `.mat` schedule + captured RNG state** | **JOP only**, and only in Time2Dist |

---

## Schedule mechanism taxonomy

| pattern | researchers | reproducibility |
|---|---|---|
| **pre-generated `.mat` + `scheduleRngState`** | JOP (Time2Dist only) | gold — `.mat` reproduces exact sequence |
| in-script `rand` matrix (per-session randperm) | BHL, BYL (PTB line), DG, JHR | partial — depends on whether the session seed is logged |
| external `condition.xlsx` loaded as resource | MSY (cat_mag / face_cond), BYL (online) | moderate — schedule deterministic; RNG state not captured |
| adaptive (staircase / PEST / Bayesian) | DG (BAM), JOP (RingRepSca train / tDCS), JOP (legacy Bhv_Mag), HJL (Main_RingExp staircase) | depends on per-trial decision log |

**Anatomist implication.** v0.1.1's PTB lens correctly treats the pre-
generated-schedule pattern as **detect-then-strict-classify** — it's a
*single-researcher convention* in CSNL, not lab-wide. The detection
trigger (`load *schedule*.mat` AND `make_*schedule*.m` exists) fires
only on JOP/Time2Dist trees. Good policy.

---

## Entry-naming taxonomy

Same code shape, many filename conventions. The anatomist's entry
detection needs to handle:

- `main_<task>.m` — JOP, JSL, MSY (PsychoJS .psyexp + .js pair)
- `mainExp_<YYMMDD>.m` — BYL (dated variants per cohort)
- `mainExp_v<N>.m` — JSL (versioned)
- `run_<TaskName>.m` — DG
- `run_<Project>.m` — JHR (run_CPS, run_restingEyeOpen)
- `psychExp_<YYMMDD>.m` — HJL, KY:BPR
- `<Project>Exp<N>.m` — KY:PBPC (PBPCExp1/2/3)
- `d2e_v<N>_<descriptor>.m` — BHL
- `Bhv_main_<task>.m` — JOP legacy
- `{task}_ses{N}_experiment.js` — MSY PsychoJS

Combined regex hint for run-time entry candidates:
```
(main|mainExp|run|psychExp|Bhv|d2e)(_v?\d+)?(_[A-Za-z0-9_]+)?\.(m|py|js)
```
Plus PsychoJS triplets `*_experiment.{js,psyexp}` + `index.html`.

---

## Helper-file naming categories (universal across researchers)

| category | examples |
|---|---|
| setup / parameter | `param_*.m`, `Init_*.m`, `load_*.m`, `setup_*.m` |
| stimulus generation | `StimGenerator_*.m`, `make_*.m`, `createStimTexture_*.m`, `generate_*.m` |
| response capture | `response_while_*.m`, `getKeyResp*.m`, `report_*.m`, `get_*.m` |
| trial / block logic | `trial_*.m`, `block_*.m`, `Duration_*.m`, `setup_*.m`, `ftn_WM_*.m` (KY), `task_funcs/*.m` (DG), `lib/init_*.m` (JHR), `taskTemplate*.m` (HJL) |

---

## Analysis-exclusion signatures (what NOT to ingest as experiment code)

The anatomist's exclusion gate must catch these even when they sit
inside an "experiment" directory:

### Neuroimaging Python
`nibabel`, `nilearn`, `statsmodels.stats.multitest`, HCP-MMP1 ROI
parcellation, BIDS / fMRIPrep, `MMP_visualize`, `Surf_template`,
`.nii` references without a stimulus loop.

### MATLAB fitting / simulation
`fminsearch`, `MCsimulation.m`, `RL_paramEst_*`, `RLmodel_*`,
`CURBD_example.m` (RNN sim), `BlahutMICD`, BAM particle-filter
*post-hoc* (note: BAM as a LIVE Bayesian adaptive trial loop IS
experiment code — distinguish by whether `Screen` is opened).

### Eye-tracking post-processing only
`tBytAnalysis*.m`, `PupilAnls.m`, `pupilPreprocessing.m`,
`*_eyeprepro.m`, `.edf` parsing scripts without live experiment.

### Stimulus preprocessing (image / table builders)
`cropping.m`, `luminance_contrast.m`, `de_padding.m`,
`generateNoisePatches.py` (offline), `generateTrialConditions*.py`
(one-shot table builder, runs once before recruitment).

### Data exploration / notebooks
`analysis.ipynb`, `Analysis.ipynb`, `PreferenceSummary.py`,
`tBytAnalysis_JR.m`.

### Legacy / staging markers in path
`*_backup_<date>/`, `Old_*/`, `archive/`, `legacy/`, `deprecated/`,
`*.asv`, `_oldmonitor_*`, `*-legacy-browsers.js`, `subjData_old/`,
`*_temp_experiment/` (when a non-temp sibling exists),
`.svn-base` files.

---

## EyeLink integration patterns

- Conditional gate: `expParam.useEyeTracker` / `exp_opt.Eyelink_TurnOn` / `useEyelink`.
- Per-trial markers: `Eyelink('Message', '<phase>')` at fixation /
  stim-onset / mask-onset / response.
- EDF filename: `<subjID_short_8char><date_or_run>.edf` (EyeLink's
  8-char limit).
- Calibration variants visible across researchers: 9-point
  (`eyeCalib9.m`, HJL), ASL legacy (`eyeCalibrationASL.m`), EyeLink
  current (`eyeCalibrationEyelink.m`, JSL/JOP), drift correction
  after >3 fixation failures (JSL).
- Live gaze gating (trial restart on deviation): JOP tDCS + KY
  MJ_OriEst; rare elsewhere.
- **Negative**: PsychoJS lines (MSY, HSL_MSY) never integrate EyeLink
  — online deployment precludes it. Useful platform signal.

---

## mgl as a separate CSNL framework

HJL alone uses **mgl** (MATLAB OpenGL wrapper) — not PTB. The callback
architecture differs materially:

- `mglOpen(...)` ↔ `Screen('OpenWindow', ...)`
- `mglFlush` ↔ `Screen('Flip', ...)`
- `mglBltTexture` ↔ `Screen('DrawTexture', ...)`
- `mglGetKeyEvent` ↔ `KbCheck(-1)`
- `initTask/updateTask/tickScreen` callback loop (no explicit
  outer `for iR` / `for iT` — the framework drives it)

**Anatomist gap.** The v0.1.1 PTB lens doesn't recognize mgl.
Either (a) extend the PTB lens with an "mgl variant" subsection, or
(b) add a parallel `prompts/lenses/mgl.md`. Detection signal:
`mglOpen(`, `mglFlush(`, `initTask(`, `taskTemplate*.m` files.

---

## Special workspace patterns

### `HSL_MSY/` — data-only joint workspace

No experiment-run code on volume. `PreferenceSummary.py` is post-hoc
analysis of CSVs from a jsPsych task hosted externally (likely
Pavlovia / Prolific / Cognition.run). The plugin must treat
**"data-only project, code elsewhere"** as a valid spec state —
`platform.framework="jspsych"` with a `note` that the code source is
external + an `open_question` asking for the upstream URL.

### `<Researcher>_<Researcher>/` joint folders

`HSL_MSY` follows a `<INIT>_<INIT>/` convention indicating joint
ownership. Likely future occurrences (e.g. `JOP_MSY/`, etc.) will use
the same. The plugin's `provenance.researcher_initial` should accept
either a single initial or a `_`-joined pair.

### Build-infra dirs (HJL `BRL_fMRI/`)

1800+ files of pure `setuptools/` Python build infrastructure with
no experiment code. The agent correctly excluded it. Detection signal:
`setup.py`, `pyproject.toml`, `*.egg-info/`, `setuptools/` subdir.

---

## Key observations for lens / harness tuning (v0.2 candidate)

1. **mgl support**: HJL's whole corpus needs a lens. Add
   `prompts/lenses/mgl.md` OR extend PTB lens with mgl section.
2. **PsychoJS Builder export awareness**: MSY's 4000+-line auto-
   generated `.js` files use `Scheduler` / `flowScheduler` abstraction
   — current PsychoPy lens covers `.py` but not the export. Extend
   PsychoPy lens with a `### PsychoJS Builder export` subsection.
3. **External condition `.xlsx`**: a SEPARATE schedule pattern from
   pre-generated `.mat`. Detection: PsychoPy `data.importConditions`
   OR PsychoJS resource loading of `.xlsx`. Outcome:
   `factor.level_source='conditions-file'`, levels list documented in
   description with note "values inside CSV".
4. **Adaptive procedures**: DG BAM, JOP RingRepSca train, HJL
   staircase — `level_source='adaptive'` and an `open_question`
   asking for per-trial decision log path.
5. **External-host pattern (HSL_MSY)**: support
   `platform.runtime_location=null` + an `open_question` for the
   upstream URL.
6. **Joint-author initials**: schema-side, accept `_`-joined initials
   in `provenance.researcher_initial`.
7. **Versioned dated entry files**: many researchers use
   `<runner>_<YYMMDD>.m` as poor-man's git. Anatomist should pick the
   *latest mtime* as canonical AND list the others in
   `provenance.notes` as siblings.
8. **Build-infra rejection**: add `setup.py`/`pyproject.toml`/
   `*.egg-info/` to the exclusion gate.

These eight items are the v0.2 backlog. None require a schema break.

---

## Per-researcher capsule (one line each)

- **BYL** — Gabor orientation discrim, PTB MATLAB (dated mainExp_YYMMDD) + PsychoPy Builder online dual-export with `trial_conditions.xlsx`.
- **BHL** — Distractor effect, PTB MATLAB, four `d2e_v<N>_<descriptor>` versions; in-script `rand` matrices, no external schedule, two-phase trials (discrim → estimation).
- **DG** — Phoneme / serial dependence / categorical, PTB MATLAB, `run_<TaskName>.m` entries with `setup/` + `task_funcs/` + `eyelink/` hierarchy. BAM is live Bayesian adaptive.
- **JHR** — Retinotopy + perceptual psychophysics, PTB MATLAB, `run_CPS.m`/`CPS2_v2.m`, factorial design in-script, fMRI-adjacent.
- **HSL_MSY** — Joint workspace, **DATA + ANALYSIS only**. The jsPsych granularity-rating task lives off-volume.
- **JOP** — Time / magnitude / scaling, PTB MATLAB. **Only researcher with pre-generated schedule pattern** (`make_trial_schedule_*.m` → `trial_schedule.mat` + `scheduleRngState`). Multi-project (Time2Dist, tDCS, RingRepSca).
- **JSL** — Serial dependence spatial, PTB MATLAB + EyeLink HD, `mainExp_v5.m`, fixed timing pipeline, drift-correction-on-fail.
- **KY** — Contrast / brightness / pupil / oddball / WM, PTB MATLAB heterogeneous, multiple paradigms (PBPC, BPR, CuBE, MJ_OriEst, AOT), all-MATLAB no JS.
- **MSY** — Face/category × magnitude, **100% PsychoJS** (PsychoPy 2025.2.3 Builder export), 4-session design with M/F variants, Prolific deployment, stimulus prep in MATLAB outside experiment.
- **HJL** — Perceptual decision-making / psychophysics, **mgl** (not PTB) with `taskTemplate*.m` callback framework; multi-decade codebase (2010-2012 dated variants) with SVN-era artifacts.
