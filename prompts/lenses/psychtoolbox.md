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

### Common pitfalls

- `par.tp` struct flattened to one entry — split per-channel.
- `subID`/`day`/`dist` missing from saved_variables (they're in
  `finalState` — count them).
- Header comments like `% Timing: tprecue 0.5->0.3` are CHANGE LOGS, not
  current values. Use the body assignment.
