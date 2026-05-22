# Psychtoolbox / MATLAB lens

Use when `platform.framework == "psychtoolbox"`. Load before Passes 3–7.

## Encoding map

- **Trial loop**: `for iT = 1:nT` (innermost). **Block loop**: `for iR = 1:nBlocks` (outer).
- **Session axis**: `par.day`, `par.session`, `expInfo.session`.
- **Mode branches**: `if isexercise`, `if isdemo` — usually a different
  `nT/nBlocks`. Treat as separate phases.

### Factors

- `mod(subjNum, N)` → `between_subject`.
- `if par.day == N` → split `meta.block_phases` (training vs test day).
- `par.StairTrainTest = [1 1 2 2 3 3]` → `within_session` block-kind factor.
- `par.X = N * ones(1, nBlocks)` → **constant parameter**, NOT a factor.
- `mod(subjNum, N)` / `pat = patList{...}` → `between_subject`. Record
  the mapping in `design_matrix_summary`.

### Per-trial saved variables (the big miss area)

CSNL convention puts per-trial data under:

- `par.X{iR}(iT)`, `par.results.X{iR}(iT)`, `par.X(iR, iT)` →
  category `stimulus`/`response` depending on the field name.
- `par.tp.X{iR}(iT)` — timing **cell-of-cell**. Each channel
  (`vbl_start`, `vbl_cue`, …, `vbl_resp`, `tend`) is its OWN entry —
  do not collapse them into a single struct entry.
- `par.results.X(iR)` (no iT) → `per_block` summary.
- `par.subID|subjNum|day|dist|expType|isexercise|isdemo|time_start|
   rng.runStart|rng.runEnd` → `per_session` `session_meta`.
- `save('foo.mat', 'finalState')` — `finalState` itself is ONE entry of
  format=struct PLUS the major sub-fields as separate per-session entries.

### Kinematic / motion IVs (often missed)

In motion-reproduction experiments:

- `par.trial.tvm1`, `par.kin.speed1`, `par.stim.dir1`, `start1`, `end1`,
  `occ_deg`, `sca_bound1`, `eyepos`, `handpos` …
- These define what is *shown*, are per-trial, and live in a separate
  generator file the entry doesn't directly call (often reached via
  `addpath(genpath(...))`).
- Pull the generator file into the bundle (look for filenames matching
  `StimGenerator*`, `*Trajectory*`, `*Kinematic*`, `*Occlusion*`).

### Display

- Participant: `Screen('DrawTexture'/'DrawDots'/'DrawLines'/'FillRect'/'Flip'/'DrawText')`,
  `DrawFormattedText`.
- Experimenter figures: `figure`, `plot`, `imagesc`, `errorbar`,
  `histogram`, `saveas`, `print -d`, `exportgraphics`. Each `saveas`
  output goes into `display.figure_outputs` with its filename pattern
  as the `sink`.

### Reproducibility hooks

- Seed: `rng(<source>)`. Score on `<source>`: `subjNum` /
  `subjNum*day` → deterministic per-subject; `'shuffle'` → not pinned;
  unset → not pinned and low score.
- Randomization: `Shuffle()`, `randperm()`, `randi()`, `randn()`, or
  fully fixed schedule (`patList{...}`).
- Version pinning: MATLAB itself isn't pinned outside Docker; rely on
  `PsychDefaultSetup` version string in `Screen('Version')`. Note in
  `environment_capture.files_found` if any `requirements.m` /
  `setup_environment.m` documents PTB version.

## Pre-generated schedule pattern (CSNL convention; detect-then-strict)

A common CSNL pattern: a separate file (e.g. `make_schedule_<exp>.m` /
`seed_<exp>.m` / `generate_<exp>_schedule.m`) is run ONCE at recruitment
to produce a per-subject trial schedule. It saves:

- the stimulus list (each block × trial)
- the day-to-condition (e.g. dist) counterbalance mapping
- the RNG state at generation time
- (optional) per-day phase flags (training vs test)

into a `.mat` file (typically `trial_schedule.mat`) that the main
script `load`s at session/block start and **replays deterministically**
— no per-trial randomization in the run-time loop.

### Detection (AND of two file-level signals)

The struct-name and field-name are NOT reliable signals (each lab/
researcher names them differently — `par.schedule.*`, `par.cb.*`,
`par.trialList.*`, bare struct, …). Trigger ONLY when BOTH of these
fire — never on struct name alone:

1. **`load(... *schedule*.mat ...)` call** somewhere in the entry or
   its 1-hop callees. Regex: `\bload\s*\(\s*[^)]*schedule[^)]*\.mat`.
2. **A generator file exists in the tree** matching
   `(make|generate|build|prep|seed)_?.*(schedule|trial).*\.m` (case-
   insensitive). Pull it into the bundle at *high priority* (the
   bundler's domain-supplement pass should bonus it heavily).

When both fire, the pre-generated schedule pattern is ACTIVE. Apply
the rules below; otherwise stay on the default RNG-sampled assumption.

### Classifications enforced when ACTIVE

- **factor.level_source** = `"inline-literal"` for any factor whose
  per-trial value is read from the loaded schedule (the levels are
  baked into the `.mat` — the run-time code reads, doesn't sample).
- **reproducibility.randomization.scheme** = `"fixed_schedule"`.
- **reproducibility.seed.pinned** = `true`,
  `source = "saved RNG state in <schedule-file> (par.scheduleRngState
  or equivalent)"`,
  `scope = "per_subject"`. Award the FULL seed component (25/25) and
  the FULL randomization component (15/15) — this is the GOLD-standard
  reproducibility pattern; a stranger with the `.mat` reproduces the
  exact sequence.
- **saved_variables MUST include** at least:
  - one entry of `scale=per_subject, category=session_meta, format=struct`
    pointing at the schedule (sink = the loaded `.mat` path), and
  - one entry of `scale=per_subject, category=rng_state, format=struct`
    pointing at the captured RNG state field.
- **parameters MUST include** a `shape="input"` entry naming the
  schedule file path (the runtime loads it).
- **design_matrix_summary**: read the **generator source** (#2 above)
  to fill this. The schedule `.mat` alone only stores the *resolved*
  mapping — the *scheme* lives in the generator code.
  - If the generator file is NOT in the bundle (e.g. supplement
    couldn't fit it), set `design_matrix_summary = null` AND queue an
    `open_question` with topic=`conditions`:
    "schedule generator 소스가 번들에 없음 — counterbalance 매핑 패턴을
    직접 알려주세요 (예: subjNum mod N → ?)".

### Counterbalance — within-subject vs between-subject (inside the generator)

`make_schedule_*.m` is where the scheme is decided. Read it carefully:

- **Within-subject CB**: the generator loops over `day` and assigns
  per-day conditions per subject. Example: `dist` ∈ {A, B} with each
  subject seeing 2 A-days + 2 B-days during Days 2-5 (TimeExp2 pattern).
  → `factor.role = within_subject`, conditions[] lists each dist *once*
  with description noting "realized on N of M days; mapping per subject".
- **Between-subject CB**: the generator branches on subject identity
  (e.g. `mod(subjNum, N)`) and assigns the same condition for all
  days of that subject. → `factor.role = between_subject`,
  conditions[] differentiates per-subject groups.
- **Both / mixed**: nested — outer subject grouping, inner day rotation.
  Describe both in `design_matrix_summary` verbatim.

The *test* is: does the generator iterate per `(subj, day)` and write
day-varying values into the schedule (within-subject), or does it
pick a constant per `subj` (between-subject)? Read the generator's
outer loops.

### Hierarchy counts — literal first, schedule dims as sanity

When the pattern is ACTIVE:

- **Read n_blocks / n_trials_per_block from literal constants** in the
  entry / setup file (`nBlocks = 12`, `nT = 40` etc.) — these are the
  authoritative source.
- Read `length(par.schedule.X)` AND `length(par.schedule.X{1})`
  *additionally* and cross-check. If schedule dims differ from the
  literal constants, the schedule wins for the actual run (the loop
  iterates `1:length(...)`), but log the mismatch:
  - record both values in evidence,
  - set the static check `schedule_consistency = false`,
  - queue an `open_question` with topic=`hierarchy`.
- If literal constants are absent (loop literally `for iR=1:length(par.schedule.Stm)`),
  read from schedule dims and note that as the authoritative source.

### Common pitfalls

- `par.tp` struct flattened to one entry — split per-channel.
- `subID`/`day`/`dist` missing from saved_variables (they're in
  `finalState` — count them).
- Header comments like `% Timing: tprecue 0.5->0.3` are CHANGE LOGS, not
  current values. Use the body assignment.
- **Pre-generated schedule misclassified as RNG-sampled**: if
  `load *schedule*.mat` + a generator file are both present, the
  per-trial values are NOT sampled at runtime. Factor `level_source`
  must be `inline-literal`, not `rng-sampled`. Reproducibility seed
  gets FULL credit, not partial.
- **Within-subject CB mistaken for between-subject**: if the
  generator iterates per-(subj,day) and rotates conditions across
  days, that's `within_subject`. Only when the generator picks a
  constant per-subject is it `between_subject`.
- **Inventing trial counts**: never fill `n_blocks` / `n_trials_per_block`
  from intuition or sibling experiments. Either read literals from
  the entry/setup OR leave null + queue `open_questions[]`. (No
  invention is a hard rule.)

## Adaptive procedures (staircase / Quest / Bayesian)

When the trial loop computes the next stimulus level from past
responses, treat the procedure as **adaptive** and emit
`adaptive_procedure` info. Three flavors recur:

### Up/down staircase (Levitt 1971 family)

Detection (any of):

- `upDownStaircase(nup, ndown, init, step, ruleSelector)` (mgl / Gardner-
  ported helper)
- `Staircase(...)` / `Palamedes`-style staircase wrappers
- Hand-rolled pattern: `if k_correct >= ndown → step -1`,
  `if k_incorrect >= nup → step +1`, `reversal counting → halve step`

Extract:

- `procedure_family = "staircase"`
- `update_rule = "<nup>-up-<ndown>-down <ruleName>"` where ruleName ∈
  `{none, levitt, pest, garcia-perez-weighted}`. **Don't merge** Levitt
  with PEST — they have different convergence behavior:
  - 1u1d → 50 %
  - 1u2d → 70.7 % (Levitt) or 75 % (Wetherill 1965)
  - 1u3d → 79.4 %
  - 3d1u → 79.4 %
- `step_size_rule`: Levitt halves on reversal indices `2^k - 1`
  (1, 3, 7, 15, ...); PEST halves on every reversal AND doubles after
  N same-direction steps; Garcia-Perez uses asymmetric Δup ≠ Δdown.
- `n_interleaved_staircases`: count of parallel staircases when
  `multipleStaircase` / equivalent randomly picks among N staircases
  per trial. The keying variable (which staircase per trial) IS a
  within-trial factor — note it.
- `termination`: `n_reversals`, `n_trials`, or `asymptote_criterion`.
  HJL/Main_RingExp terminates on outer trial count, not reversal count;
  `computeThreshold(staircase, targetP, ...)` and
  `meanOfLastNReversals` outputs are **post-hoc analysis convenience**,
  not runtime stopping rules — don't infer "stop after k reversals"
  from their existence.

Reproducibility:

- The trajectory depends on the subject's **binary responses**, which
  are NOT in the RNG stream. Replay requires saving `s.response[]`,
  `s.strength[]`, AND init params (thresh, stepsize, rule, up/down).
- Score `randomization = "fixed_schedule"` for the *next-level
  derivation* ONLY when these are saved. If only the final threshold
  estimate is saved, downgrade to `"partial — trajectory not
  recoverable"`.

### Quest (Watson & Pelli 1983) / QUEST+

Detection:

- `QuestCreate(`, `QuestUpdate(`, `QuestQuantile(`, `QuestMean(` (PTB-
  shipped psychometric Bayesian estimator)
- `qpInitialize`, `qpListMaxArg`, `qpQuery`, `qpUpdate` (QUEST+,
  Watson 2017 generalization)
- Often paired with `tGuess`, `tGuessSd`, `pThreshold`, `beta`, `delta`,
  `gamma` parameters

Extract:

- `procedure_family = "quest"` or `"quest_plus"`
- `psychometric_function = "weibull"` (Quest default) or whatever the
  user passes via `qpInitialize`'s `psiParamsDomainList`
- Termination: `n_trials` (Quest doesn't auto-stop)
- Saved: typically only the final `QuestMean` / posterior summary,
  occasionally the full `quest.intensity[]` and `quest.response[]`
  arrays. The latter is the gold standard.

### Bayesian adaptive (PSI, optimal-info-gain, particle filters)

Detection:

- `psybayes(psy, method, vars, xi, yi)` (Acerbi's MATLAB PSI — direct
  Kontsevich-Tyler 1999 + Prins extensions). Method='ent' = minimum
  expected entropy.
- Custom: a function called inside the trial loop that returns
  `next_stim` from `argmin E[H(posterior | response)]` or
  `argmax I(R; θ)` (mutual-information criterion). Both compute the
  same thing in theory; recognize by signature, not by name.
- Particle-filter pattern: `mvnrnd`, `randsample(..., true, weights)`
  for resample, MH proposal step, `Theta{i_tr} = theta` per-trial
  snapshot of the particle cloud.
- Grid-posterior pattern: `prob = prob .* likelihood; prob = prob /
  sum(prob);` in the trial loop.

Extract:

- `procedure_family = "bayesian_adaptive"`
- `engine`: name the algorithm — `"psi-kontsevich-tyler"`,
  `"info-gain-grid"`, `"particle-filter-MH"`, `"qpQuest+"`,
  `"custom-<x>"`. **Bayesian Adaptive ≠ Quest** — Quest assumes Weibull
  + single threshold parameter; PF/MH operates on a multi-D parameter
  with no fixed psychometric shape. Don't merge.
- `prior_representation`: `"uniform_grid_<3D|5D>"` /
  `"gaussian_prior"` / `"mixture"`.
- `selection_criterion`: `"min_expected_entropy"` /
  `"max_mutual_information"` / `"max_expected_variance_reduction"`.
- `per_trial_state_saved`: list — `posterior_summary`, `full_particle_cloud`,
  `chosen_stim`, `response`. DG/BAM saves `Theta{i_tr}` before each
  trial's stim selection — that's the reproducibility gold standard
  for PF: full posterior trajectory, not just the final estimate.
- `termination`: `n_trials` (most common); rarely `posterior_CI` or
  `KL_threshold`.

### Reproducibility scoring for adaptive procedures

- Staircase + saved `response[] + strength[] + init` → award full
  `randomization` credit.
- Quest + saved `intensity[] + response[]` (or posterior history) →
  full credit.
- Bayesian adaptive + saved per-trial posterior summary OR full
  particle/grid snapshot → full credit. **Only final posterior saved**
  → downgrade to `"partial"` (RNG-sensitive PF/MH chain cannot be
  re-run deterministically across MATLAB versions).
- For all three: if RNG seed is not explicitly saved AND the procedure
  uses any internal random component (proposal noise, particle init),
  reproducibility drops further regardless of state-saving.

### Detection pitfalls

- A `method='random'` TrialHandler with adaptive-LOOKING variable names
  is NOT adaptive. The discriminating test is "does the level for
  trial N depend on the response on trial N-1, computed inside the
  same trial loop body?". If the level was set before the loop, it's
  constant-stimuli, regardless of how `threshold`-y the variable name.
- A file that calls `QuestUpdate` but never `QuestQuantile` is *logging*
  into Quest, not *driving* with it. Connect the chain: response →
  posterior update → next stim selection within the same iteration.
- "BADS" / "PyBADS" in the same project ≠ adaptive experimental
  procedure. Acerbi-lab's BADS is a **post-hoc** derivative-free
  optimizer over likelihood; its naming overlap with adaptive
  experimental design is misleading.
- `trial_stims(i_tr) = next_stim` overwriting a pre-allocated array
  inside the loop IS adaptive even when the surrounding code looks
  like constant-stim replay. Look for an assignment to the schedule
  inside the trial body.

## External-host pattern (data-only / code-elsewhere workspaces)

Some researchers keep only **data** locally and host the experimental
code externally (Pavlovia, OSF, a paper-companion GitHub). Detection:

- Tree contains ≥3 of: `.csv` / `.psydat` / `.mat` data files,
  README-like `.md` referencing an external URL, NO `Screen(` / no
  `visual.Window` / no `mglOpen` calls in any local file.
- The local `.md` says things like "task hosted on Pavlovia at
  pavlovia.org/<user>/<exp>" or "code archived at osf.io/<id>".

When detected, do NOT classify as "incomplete" — emit:

- `platform.framework = "external"` (new sentinel)
- `platform.external_host`: `{ kind: "pavlovia" | "osf" | "github" |
  "lab-private", url: "<url-if-found>", evidence: "<file:line>" }`
- `hierarchy`, `factors[]`, `conditions[]`: derive from the saved data
  columns + paper Methods if available.
- `reproducibility.notes`: "code hosted externally — runtime not
  inspectable from local tree"; `version_pinning` = `null` or whatever
  the external host pins.
- `open_questions[]`: queue a request for the upstream URL / paper
  Methods section / PsychoJS export so the deconstruction is complete.

This pattern is distinct from a missing-generator case — there the
local tree has the runner but is missing a `make_schedule_*.m`
generator. External-host means the **runner itself** is offsite.
