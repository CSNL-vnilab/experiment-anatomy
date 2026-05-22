# External psychophysics samples — survey summary

Companion to [`db/external-samples.json`](./external-samples.json).
Human-readable digest of a v0.2-tuning meta-search across prominent
psychophysics + perceptual-decision-making labs (Gardner, Acerbi,
Stocker, Sims, plus Brainard / Wichmann / Wei Ji Ma / Gold / Pelli /
Wandell). Companion to [`db/csnl-conventions.json`](./csnl-conventions.json)
which catalogues CSNL-internal conventions.

First run: **2026-05-22**. 5 parallel `general-purpose` Opus subagents,
~8-12 min wall-clock, ~33 catalogued samples.

## Headline counts

| Lab | Experiment-runtime samples | Paper-companion (data+model only) | Framework-only references |
|---|---:|---:|---:|
| Gardner Lab (Stanford) | 11 | 0 | mgl (canonical), pgl |
| Acerbi Lab (Helsinki) | **1** (psybayes adaptive engine) | 3 (ChangeProb, visvest-causinf, bayescausinf-models) | BADS, VBMC, PyVBMC, gpyreg, PyBADS |
| Stocker Lab (UPenn) | **0** | 4 (Self-consistent, Working-memory, Speed_Prior, adapt-discr) | — |
| Sims Lab (RPI) | 1 (fourinarow webapp tutorial) | 3 (ecpg, Human-RL-capacity, ResourceRationalCognition) | AdaCog org private |
| Brainard / Wichmann / Ma / Gold / Pelli / Wandell | 10 | 0 | BrainardLabToolbox, psychopy-pixx, snow-dots, vistadisp |

**Total catalogued samples: 33** (samples + companions). Note the
shape diversity: Gardner publishes the entire grustim repo at once;
Stocker publishes only models + data; Sims publishes data+fits but not
the frontend; Brainard publishes both with a ToolboxToolbox descriptor;
Pelli publishes one engine with ~20 thin runner wrappers.

## Schedule-mechanism taxonomy (across CSNL + external)

| Mechanism | CSNL exemplars | External exemplars |
|---|---|---|
| Pre-generated `.mat` schedule + generator + saved RNG state | **JOP Time2Dist** (canonical) | Brainard VirtualWorldPsychophysics (trialStruct.mat off-line built) |
| In-script `randperm`/`Shuffle`/`mseq` per session | HJL Main_RingExp (m-sequence via genExpBlock) | Gardner twoPatchMotionDir, sigdetect, spjdg_constant, easyhard; Wichmann (with CSV overlay) |
| External CSV/XLSX conditions table | MSY (xlsx), BYL (xlsx + hand-shuffle) | Gold DefaultBlockSequence.csv + BlockPairs.csv; Wichmann blockcount_*.csv |
| JSON config (identity + deps) | — | Gold Task_*.json (ToolboxToolbox tradition) |
| `task.parameter` factorial (mgl) | — | Gardner alaisburr, cohcon, sigdetect |
| Pre-built block-array via handwritten builder | — | Gardner afcom; Gardner cohcon |
| Cross-session posterior persistence (warm-start adaptive) | — | Ma HVI; Gardner alaisburr/cohcon/sigdetect (`getLastStimfile`) |
| Pure adaptive (no fixed schedule) | DG BAM | Pelli CriticalSpacing (Quest only); Ma HVI (PSI only) |

## Adaptive-procedure distribution

| Family | CSNL | Gardner | Other |
|---|---|---|---|
| 1-up-N-down staircase (Levitt / PEST / Garcia-Perez) | HJL Main_RingExp (1u2d Levitt × 3 interleaved) | alaisburr, cohcon, sigdetect, easyhard, wmface, geislerSearchTask, afmap | Wandell GaborStaircase |
| QUEST classic (Watson 1983) | — | sigdetect (option) | **Pelli CriticalSpacing** |
| QUEST+ (Watson 2017, `qpInitialize`) | — | — | **Gold Task_SingleCP_DotsReversal** |
| PSI (Kontsevich-Tyler / psybayes) | — | — | **Ma HVI**; Acerbi psybayes |
| Bayesian adaptive (PF + info-gain) | **DG BAM** | — | — |
| No adaptive (constant-stim) | — | gruRetinotopy, spjdg_constant, afcom | Brainard, Stocker companions, Sims |

DG's PF+MH info-gain Bayesian adaptive (in BAM) is **unique in this
33-sample catalogue**. The closest cousin is Acerbi's psybayes (PSI),
which Ma HVI uses across sessions.

## Per-lab capsules

### Gardner Lab — the mgl mainline (11 samples)

The Gardner Lab is the canonical mgl reference. Every sample in
`grustim` follows the same shape: `function myscreen = <name>(varargin)`
with `getArgs(varargin, {...defaults...})`, `task.parameter` + `task.seglen`
+ `task.getResponse` setup, callback registration via `initTask(task,
myscreen, @startSegmentCallback, @screenUpdateCallback, @responseCallback,
...)`, and the canonical `while (phaseNum <= length(task)) &&
~myscreen.userHitEsc` loop. Distinctive lab conventions:

- **Cross-run warm-start** via `getLastStimfile` + `stimulus.<X>Staircase{end+1}`.
- **Scanner-aware** — every script has `scan=0/1` flag flipping screen
  (`fMRIprojFlex` vs `VPixx`), syncing to volume triggers, disabling
  catch trials. One file ≠ one paradigm; it's one file × {psychophysics,
  scanner}.
- **Stimulus modality switches** — `visual=1`/`auditory=1`/`bimodal=1`
  (alaisburr, spjdg), `stimulusType=dots|faces|grating` (sigdetect),
  `taskType=auditory|visual` (wmface). Same file = multiple paradigms.
- **Variants by suffix** — `_metal` (new Apple Metal backend), `_constant`
  (constant-stim variant of a staircase script), `_loc`/`_localizer`,
  `fMRI`, `_<initials>` (student fork). Treat suffixed siblings as
  related, not independent.
- **Replay mode** — `replay=<filename>` + `initScreen('replayScreen')`
  re-renders offline against a saved stimfile (afcom, afmap).
- **Stimfile triple** — every analysis reads only `(task, myscreen,
  stimulus)` from `~/data/<expname>/<SID>/<timestamp>.mat`.

### Acerbi Lab — adaptive engine + post-hoc inference (1 + 3 samples)

The Acerbi Lab ships **inference tooling** (BADS, VBMC, PyVBMC, pybads)
and **paper-companion data+fitting**. Only `psybayes` is true
experiment runtime — and even it has zero PTB calls; it's an adaptive
engine designed to be called from inside a PTB or mgl trial loop.
`[xnext, psy, output] = psybayes(psy, method, vars, xi, yi)` is the
trial-loop API: caller passes back previous stim + response, receives
next stim. Method='ent' minimizes posterior entropy (Kontsevich-Tyler
1999 + Prins 2012/2013 lapse extension).

**BADS in experimental loops?** No — BADS is post-hoc derivative-free
optimization. The naming overlap with "adaptive experimental design"
is misleading; BADS's "adaptive" refers to mesh refinement inside the
optimizer.

### Stocker Lab — data + model, no stimulus code (0 + 4 samples)

**Critical finding: zero of nine inspected Stocker repos contains
stimulus-presentation code.** `grep Screen|PsychImaging|KbCheck`
returns no matches across `Self-consistent-model`, `Working-memory-
model-PlosCompBio2021`, `Speed_Prior_2021`, `adapt-discr-efficient-code`,
etc. Every release ships `.mat`/`.txt` data + MATLAB model-fitting +
figure-generation scripts. The lab's "Methods" sections describe the
PTB experimental protocol, but the code remains internal.

Distinctive shapes:

- **Folder hierarchy as factor table** — `Data/Data_Exp{n}/P{m}/{MainExperiment,
  MotorNoise,PerceptNoise,TrainArray}/Original1/Original-1.mat` —
  each path segment is a factor dimension.
- **Header-comment column dictionary** — tab-separated `.txt` with
  `% Column N: ...` preamble (Self-consistent-model).
- **Parameter-vector convention** — `paramsAll(i:j)` slices index
  condition-tied parameters; the indexing comment is the closest
  thing to a schema.
- **Borrowed-data pattern** — Speed_Prior 2022 re-analyzes Stocker &
  Simoncelli 2006 (`/behavior/NN2006/`). One repo can be a
  re-release.

License default is **none** (7/9 repos). Only 2/9 are MIT-licensed.

### Sims Lab — forced-choice + post-hoc rate-distortion fitting (1 + 3 samples)

Active code lives on student handles (`fangzefunny`, `TailiaReganMalloy`),
not on `simsc3` (empty). The lab's AdaCog org is on RPI's private
enterprise GHE and unreachable. The four catalogued samples all use
**forced-choice keypress responses**, even though Sims's theoretical
focus is rate-distortion continuous-report delayed-estimation. The
"color wheel mouse-drag" mechanism standard in Bays/Wilken literature
does NOT appear in any reachable Sims-lab repo.

`ecpg` (Fang & Sims 2025, Nat. Comm.) is the flagship paper-companion:
analysis-only on GitHub + data+fits+sims+analyses ZIPs on OSF
([uctdb](https://osf.io/uctdb/)). Frontend confirmed absent — data
schema `rt,stimulus,response,corAct,corKey,screen_id,trial` strongly
suggests jsPsych as the unreleased runtime.

### Brainard / Wichmann / Wei Ji Ma / Gold / Pelli / Wandell (10 samples)

Six adjacent labs contributing distinct release patterns:

- **Brainard**: MIT-licensed PTB + BrainardLabToolbox + ToolboxToolbox
  project descriptor (`.json` at repo root). Conditions are pre-built
  off-line (`trialStruct.mat`) — same family as CSNL TimeExp2.
- **Wichmann**: PsychoPy *coder* (not Builder), per-condition CSV
  block-counts for pseudo-adaptive block rotation, ViewPixx/ResponsePixx
  hardware presumption. License default: none.
- **Wei Ji Ma**: PTB + Acerbi's PSI (HVI) with cross-session posterior
  persistence; custom JS (not jsPsych) for online (fourinarow). Mixed
  release shape.
- **Gold**: snow-dots (`topsTreeNodeTask*` OOP scheduler) + CSV block
  sequence + JSON task identity. First-class **eye-tracker
  pluggability** at the framework layer (Eyelink / PupilLabs / EOG /
  Gamepad / Keyboard / Mouse-sim).
- **Pelli**: pure PTB, **one engine + 20 thin runner wrappers**
  (CriticalSpacing.m + runAcuity/runComplexity/runCrowdingSurvey/...).
  BIG one-struct `o.*` config (~50 fields). Quest-only adaptive.
- **Wandell** (vistadisp): **modular four-Init pattern**
  (display / stim / staircase / fix / subject — separate Init function
  per concern) + pluggable trial-generator by string name.

## v0.2 lens-tuning backlog (delivered this run)

1. ✅ **mgl lens** (`prompts/lenses/mgl.md`) — built from HJL
   Main_RingExp deep-read + Gardner Lab cross-comparison. Two-mode
   classifier (callback / primitive), factors-in-three-places rule,
   eye-tracker variant detection, adaptive subsection.
2. ✅ **PsychoJS Builder export subsection** (`prompts/lenses/
   psychopy.md` § 5) — four-file fingerprint, Scheduler /
   flowScheduler / loopScheduler model, xlsx config-as-conditions
   trick, Routine-triple grouping, auto-telemetry vs researcher-
   added columns separation, Prolific/Pavlovia integration.
3. ✅ **Adaptive-procedure subsection** in PTB lens
   (`prompts/lenses/psychtoolbox.md`) — staircase / Quest / Quest+ /
   PSI / Bayesian-adaptive families with detection signals and
   per-trial state save expectations.
4. ✅ **External-host pattern** in PTB lens — Pavlovia / OSF / lab-
   private code-elsewhere release shape, with `platform.framework =
   "external"` sentinel.
5. ✅ **Anatomist Pass 2** updated — recognizes `mgl`, `psychojs-builder`,
   `external` as distinct platforms; routes to the right lens.
6. ✅ **Factors-in-multiple-places rule** in anatomist Pass 4 —
   per-framework checklist of where factor levels can live (PTB
   schedule, mgl `task.parameter`/`randVars`/`expBlock.*Seq`,
   PsychoPy xlsx, jsPsych factorial_design).

## v0.3 lens-tuning backlog (deferred)

- **snow-dots lens** (Gold Lab pattern) — `topsTreeNodeTask*` OOP +
  DefaultBlockSequence.csv + ToolboxToolbox JSON descriptor. Distinct
  from both PTB and mgl. Worth a dedicated lens once a CSNL researcher
  adopts it.
- **One-engine-many-runners pattern** (Pelli CriticalSpacing,
  Brainard) — when a repo has `<Engine>.m` + 10+ `run<Variant>.m`,
  each variant is a separate experiment. Current lenses might collapse
  them.
- **ToolboxToolbox-managed projects** — the *real* entry call is
  `tbUseProject('<RepoName>')` before `run_task.m`. Detect via root
  `<RepoName>.json` with `'type':'git'` / `'include'`.
- **Cross-session posterior persistence** (Ma HVI, Gardner warm-start
  staircases) — distinguish "raw-data save" from "state-carry save".
  Affects reproducibility scoring (each invocation is NOT independent).
- **Stocker-shape "data+model release"** — recognize as valid release
  shape, not "incomplete experiment". The `paper_companion_only`
  flag could ride alongside `external` in the platform enum.
- **License heterogeneity warning** — surface `license: null` samples
  as a reuse risk in the anatomist's output.
- **Two-stage seed pattern** (CSNL HJL: rand draws seed → seed pinned
  downstream) — distinguish from one-stage `rng(seed)` and from
  unseeded fallback. Affects reproducibility scoring (still recoverable
  via saved seed field, but only if downstream helpers actually use it).

## Provenance

- **Run**: 2026-05-22
- **Orchestrator**: Claude Opus 4.7 (`claude-opus-4-7[1m]`) running in
  CSNL lab Claude Code session
- **Agents**: 5 parallel `general-purpose` (model=opus, read-only
  browse + WebSearch + git clone to /tmp). Agent IDs:
  - Gardner: `aa69b12c35402f313` (49 tool calls)
  - Acerbi: `a8d8b38c97c35ec63` (28 tool calls)
  - Stocker: `af3ecc12aa4454561` (28 tool calls)
  - Sims: `a1869dd313a623d78` (132 tool calls — Sims lab does NOT
    publish on its own org; agent chased student handles via paper
    citations)
  - Adjacent: `ae82b969fde91b5e3` (51 tool calls)
- **Wall-clock**: ~735 s total across 5 parallel agents (longest:
  Sims, 12 min).
- **Cloned trees** (shallow `git clone --depth=1`, retained at
  `/tmp/` but NOT committed to this repo):
  - `/tmp/gardner-{mgl,grustim}/`
  - `/tmp/acerbi_probe/{psybayes, ChangeProb, visvest-causinf,
    bayescausinf-models, neurobench}/`
  - `/tmp/stocker_probe/{Self-consistent-model,
    Working-memory-model-PlosCompBio2021, Speed_Prior_2021,
    adapt-discr-efficient-code}/`
  - `/tmp/sims-meta/{fourinarow-replication, ecpg, Human-RL-capacity,
    ResourceRationalCognition}/` + `/tmp/sims-meta/uctdb_data.zip`
  - `/tmp/lab-meta/{CriticalSpacing, Horizontal-Vertical-Illusion,
    Task_SingleCP_DotsReversal, VirtualWorldPsychophysics,
    scaling-dimension, vistadisp}/`
- **Primary sources** (canonical upstream — verifiable):
  - GitHub orgs: justingardner, acerbilab, lacerbi, cpc-lab-stocker,
    BrainardLab, wichmann-lab, WeiJiMaLab, TheGoldLab, denispelli,
    vistalab
  - GitHub personal handles: fangzefunny, TailiaReganMalloy
    (Sims-lab student forks)
  - OSF: [uctdb](https://osf.io/uctdb/) (Sims ecpg 2025),
    [x5ckn](https://osf.io/x5ckn/) (Sims 2018 Science)
  - Lab sites: gru.stanford.edu (mgl docs), sas.upenn.edu/~astocker,
    adacog.com (Sims publications)
  - PMC: [PMC12037794](https://pmc.ncbi.nlm.nih.gov/articles/PMC12037794/) (Fang & Sims 2025)
- **Per-sample evidence fields** cite real `file:line` refs within
  those clones; URLs above are the canonical upstream for verification.
- **No data modified** at any cited URL — all reads are read-only or
  shallow-clone-and-Read.
- **Findings folded** into v0.2 lenses + this commit's schema 1.1.0
  + v0.3 backlog above.
- **Replicability**: re-run via
  [`scripts/scan-external-samples.md`](../scripts/scan-external-samples.md)
  harness. Expect numbers to drift as labs publish new repos.

## Related

- [`db/csnl-conventions.json`](./csnl-conventions.json) +
  [`db/conventions-summary.md`](./conventions-summary.md) — CSNL-internal
  conventions survey (10 researchers, 2026-05-22)
- [`scripts/scan-csnl-conventions.md`](../scripts/scan-csnl-conventions.md) —
  reproducible recipe for the CSNL-side survey
- [`scripts/scan-external-samples.md`](../scripts/scan-external-samples.md) —
  reproducible recipe for this external-side survey
