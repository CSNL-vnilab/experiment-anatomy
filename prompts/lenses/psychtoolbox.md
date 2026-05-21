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
