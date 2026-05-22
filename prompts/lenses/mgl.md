# mgl (Justin Gardner) lens

Use when `platform.framework == "mgl"`. Load before Passes 3–7.

mgl is a MATLAB OpenGL framework (Gardner et al. 2018, DOI
10.5281/zenodo.1299497, GPL). It is the canonical stimulus stack of the
Gardner Lab (Stanford) and the historical input of Heeger / Wandell /
several psychophysics labs. In CSNL it is used by HJL's `Main_RingExp`
tree and is **not** Psychtoolbox — overlapping primitives but a different
trial-loop architecture, different state model, and different save
contract. A naive PTB lens will mis-extract every count, factor, and
reproducibility signal on mgl code.

## Two-mode classifier (mandatory first step)

mgl code comes in two flavors that the lens MUST distinguish, because
the trial-count and factor extraction rules differ:

### Mode A — `mgl-callback` (canonical Gardner Lab pattern)

Fires when the entry file contains **all** of:

- `initScreen` (no `()`-args common) OR `myscreen = initScreen;`
- `task{n}.{segmin|seglen|segmax}` field assignments
- `task{n}.{getResponse|parameter|randVars}` field assignments
- `initTask(task{n}, myscreen, @startSegmentCallback, ...)` with at
  least 3 callback handles
- The canonical loop:
  ```matlab
  while (phaseNum <= length(task)) && ~myscreen.userHitEsc
    [task myscreen phaseNum] = updateTask(task,myscreen,phaseNum);
    myscreen = tickScreen(myscreen,task);
  end
  ```
- `endTask(myscreen, task)` after the loop

Trial counts come from `task.numTrials` (literal or computed from
`task.parameter` cardinality × `task.numBlocks`), NOT from a `for`
loop. The framework default is `task.numTrials = inf`, in which case
the budget is set by `task.numBlocks * prod(numel(task.parameter.X))`.

### Mode B — `mgl-primitive` (HJL Main_RingExp pattern)

Fires when the file contains mgl primitives **without** the task
framework:

- ≥4 of `mglOpen( | mglFlush; | mglClearScreen | mglCreateTexture( |
  mglBltTexture( | mglGetKeys( | mglGetKeyEvent( | mglWaitSecs( |
  mglSetGammaTable( | mglClose | mglScreenCoordinates`
- AND **none** of `initTask(`, `updateTask(`, `tickScreen(`,
  `@startSegmentCallback`
- AND an explicit `for iT = 1:numTrial` (or equivalent) trial loop in
  the runner

Trial counts come from a pre-built schedule (`length(expBlock.contSeq)`,
`length(par.schedule.X)`) AND/OR a literal `numBlocks * trialsPerBlock`.
Look for a `genExpBlock*.m` / `multipleStaircase.m` helper that builds
the per-block sequence (often using m-sequences via `mseq(...)` —
deterministic-randomized, NOT uniform).

### Mode C — `mgl-hybrid` (HJL Main_RingExp canonical case)

The most common real-world pattern when both Mode A and Mode B
signals appear in the **same directory**:

- The chosen entry file (e.g. `psychExpPDM.m`) is pure Mode-B
  (primitives + `for iT = 1:nT` loop, no `initTask` call).
- BUT the same directory contains framework files
  (`taskTemplate.m`, `initTask.m`, `updateTask.m`, `tickScreen.m`,
  `endTask.m`) — these are **library includes, not entries**.

A naive classifier sees both sets of signals and either picks the
wrong mode or refuses to classify. The correct disambiguation is
**call-graph-aware**:

1. Pick the canonical entry per § "Canonical entry-point picker"
   below. Skip `taskTemplate*.m`, conflicted-copy siblings, `*~`,
   `*.svn-base`.
2. Walk the entry's call graph (1-hop callees). Determine whether
   the entry's actual control flow uses `initTask` + the `while
   ... updateTask ... tickScreen ... end` loop. If yes → Mode A.
   If no (the entry uses an explicit `for iT = 1:nT` even though
   framework files exist nearby) → Mode B.
3. When this divergence holds — entry is Mode B but framework
   files coexist — set `platform.variant = "mgl-hybrid"`. Apply
   the mgl-primitive rules for trial counting (`length(expBlock.contSeq)`)
   and factor extraction (`expBlock.*Seq` built by `genExpBlock` /
   `mseq`), NOT the callback rules. Note `platform.evidence` with
   "framework files present but entry uses primitive-mode loop".

This is the load-bearing rule that prevents misclassifying
HJL/Main_RingExp's `psychExpPDM.m` as Mode A (which would have the
lens look for `task.parameter` factors that don't exist) or refusing
to classify (which would drop the project into `unknown`).

### Negative-signal check (rule out PTB)

If the file ALSO contains `Screen('OpenWindow'`, `Screen('Flip'`,
`KbCheck`, `KbWait`, or `PsychDefaultSetup`, demote the verdict to
`ptb-mixed` and warn. mgl and PTB are mutually exclusive in well-formed
code; their co-occurrence is usually a porting attempt or accidental
import.

## Encoding map

### Trial loop — callback world

There is no `for iT = ...` in Mode A. The loop is `while (phaseNum <=
length(task))` driven by `updateTask` / `tickScreen` returning. The
trial counter lives in `task{n}.trialnum` (incremented inside
`updateTask`), block counter in `task{n}.blocknum`.

Per-trial volatile state on `task.thistrial`:

- `task.thistrial.thisseg` (current segment within trial)
- `task.thistrial.<param-name>` (one entry per `task.parameter.X` field)
- `task.thistrial.<randvar-name>` (one entry per `task.randVars.*.X` field)
- `task.thistrial.gotResponse`, `whichButton`, `reactionTime`, `seglen`,
  `segstart`

`task.thistrial.<name>` for every `task.parameter.<name> = [...]` is
**not** the same as a within-trial factor — it's how the framework
exposes the current trial's sampled value to user callbacks.

### Segment / timing model

mgl encodes time as **segment durations within a trial**, not as a
single trial duration:

- Fixed: `task{1}.seglen = [1 0.5 0.25 0.5 1.5];` (5 segments)
- Variable: `task{1}.segmin = [3 6]; task{1}.segmax = [3 9];`
- Quantized random: add `task{1}.segquant = [0 1.5];` to draw from
  `{6, 7.5, 9}` instead of uniform
- fMRI synch: `task{1}.waitForBacktick = 1; task{1}.synchToVol = [0 1];`
  — segment 2 advances on the next scanner volume pulse

Emit each segment as one row of the timing table (segment idx → min →
max → response-allowed? from `task.getResponse`).

### Factors — three places, not one

Always check all three before concluding "no factors":

1. `task{n}.parameter.<X> = [levels];` + `task{n}.random = 1;` →
   **crossed within-trial factor**, levels = the assigned array.
   `level_source = "inline-literal"`.
2. `task{n}.randVars.uniform.<X> = [levels];` → **uniformly sampled
   per-trial factor**, treated as `level_source = "rng-sampled"` on
   the listed levels. Variants: `randVars.block`, `randVars.calculated`
   (the last is a *slot for response/RT*, NOT a factor — emit only as
   `saved_variables`).
3. Pre-built sequences read from `expBlock.<X>Seq` (HJL/mgl-primitive
   pattern) — built by `genExpBlock*.m` or sibling generator,
   level enumeration lives in the generator source. Same rules as the
   PTB pre-generated-schedule pattern (`level_source = "inline-literal"`,
   `randomization.scheme = "fixed_schedule"` if the generator stores
   seed/state alongside).

If `task.parameter` is empty AND `expBlock.*Seq` is empty AND no
in-loop `randperm`/`mseq`/`Shuffle`, the experiment has no manipulated
factors — emit `factors: []` and queue an `open_question` clarifying.

### Per-trial saved variables (the canonical mgl save contract)

`endTask(myscreen, task)` triggers `saveStimData`, which writes
`YYMMDD_stim<NN>.mat` under `myscreen.datadir` (default `~/data/<expname>/<SID>/`).
The saved bundle is `myscreen`, `task`, and any `stimulus` global.

Per-trial information is reconstructable from saved `task` via
`getTaskParameters(myscreen, task)` (an mgl utility that walks
`task.parameter` + `task.randVars.calculated` into one-row-per-trial).
Specifically:

- Every field of `task.parameter` ships per-trial (cardinality =
  `task.numTrials × task.numBlocks`).
- Every field of `task.randVars.calculated` ships per-trial (these are
  the response slots: `resp`, `correct`, `rt` typically).
- `task.private` is a user-defined slot for block-level constants
  (recognized by the field validator but rarely populated — note as
  uncertain unless evidence found).

For mgl-primitive code (HJL Main_RingExp), the per-trial save is
**explicit** — e.g.

```matlab
save([saveDir '/' saveFileName], 'expEnv', 'expData', 'staircase');
```

with `expData.{pracData|thEstData|mainData}{iB}` being `numTrial × 10`
matrices whose columns are documented in the runner header
(typical layout: `[image, stepIdx, cue, stimulus, correct, response,
rt, trialOnset, secondKey, secondKeyTime]`).

### Display

- Stimulus: `mglCreateTexture(image_uint8)`, `mglBltTexture(tex, [x y], hAlign, vAlign, rotation)`,
  `mglFlush;` (vs PTB's `Screen('Flip')`).
- Text: `mglTextSet(font, size, color)` + `mglTextDraw(str, [x y])`.
- Fixation primitives: `mglFixationCross`, custom `showFixation` utilities.
- Experimenter figures: `figure`, `plot`, `imagesc`, `saveas` (same as
  PTB lens) — emit into `display.figure_outputs`.

### Eye-tracker variants

mgl wraps three eye-tracker families with separable calibration helpers:

- **EyeLink (SR Research)**: `mglEyelinkSetup()`, `mglPrivateEyelink*`,
  `eyeCalibrationEyelink.m`. Console-based 9-pt calibration.
- **ASL (Applied Science Laboratories)**: `writeDigPort(...)` for stim
  marker pulses, `eyeCalibrationASL.m`.
- **9-pt manual**: `eyeCalib9.m` — `myscreen.eyecalib.x = [5 0 -5 ...]`
  9-point grid, no live tracker integration.

Differentiator for the lens:

- `mglEyelinkSetup(` → EyeLink (auto-tracking).
- `writeDigPort(` + `eyeCalibrationASL` or `eyeCalib9` → ASL or manual.
- No `eyeCalib*` call in canonical entry → "no eye tracking" (common
  for psychophysics rigs).

Calibration is dispatched via `eyeCalibDisp(myscreen)` — its presence
in the entry's call graph is the gate signal. **HJL psychophysics
scripts never call `eyeCalibDisp`** — the lens must not over-promote
"mgl + eye tracker present in dir" to "eye tracking active".

## Reproducibility hooks

### Seed pinning

- mgl-primitive (HJL): two-stage. The seed is **drawn from the un-seeded
  RNG** at script-top, then used to seed both `rand` and `randn`:
  ```matlab
  expData.seedRand = ceil(rand(1) * 10000);
  randn('state', expData.seedRand);
  rand('state', expData.seedRand);
  ```
  The seed itself is saved in `expData.seedRand`. Reproducibility
  requires loading the seed from the `.mat`, not rerunning the script.
  Score: `pinned=true, source="run-time draw saved into expData.seedRand",
  scope=per_session`. Award FULL credit only if the seed is also passed
  to downstream helpers like `genExpBlock(numSet, expMode, seedRand)`.
- mgl-callback (Gardner): typically `randstate = rng;` at entry +
  `task` framework records its own per-segment RNG calls. Less explicit
  than HJL's two-stage pattern.
- mgl framework files (`taskTemplate.m` etc.) ship SVN `$Id$` keywords
  for version pinning — note in `environment_capture.files_found` if
  present.

### Randomization scheme

- `task.random = 1` + `task.parameter.X = [...]` →
  `scheme = "random_permutation_per_block"`.
- `task.randVars.uniform.X` → `scheme = "uniform_per_trial"`.
- `mseq(base, power, n, seed)` (HJL via `genExpBlock`) →
  `scheme = "m_sequence_predetermined"`, fully reproducible.
- `randperm(N)` in a helper that builds `expBlock.*Seq` →
  `scheme = "fixed_schedule"` (pre-built once, replayed verbatim).

### Cross-run / cross-session state

Gardner Lab uses `getLastStimfile(myscreen)` + `stimulus.<X>Staircase{end+1}`
to **warm-start adaptive procedures across runs**. When detected,
mark `reproducibility.notes = "warm-start adaptive from prior stimfile"`
— this means the script's behavior depends on past saved files, not
purely on the current invocation.

## Adaptive procedures

mgl ships `upDownStaircase.m` (Levitt 1971 transformed up/down with
`'levitt'` and `'pest'` rule selectors) and `doStaircase` wrapper
(Gardner-lab convention). Detection + extraction:

- `upDownStaircase(nup, ndown, init, step, ruleSelector)` →
  - `procedure_family = "staircase"`
  - `update_rule = sprintf("%d-up-%d-down %s", nup, ndown, rule)`
    where `rule ∈ {none, levitt, pest}` from the 5th arg
  - Convergence target: 1u1d → 50%, 1u2d → 70.7%, 1u3d → 79.4%,
    3d1u → 79.4% (cite the rule, not a guessed target)
- `multipleStaircase(mode, params)` (HJL) — **multiple interleaved
  staircases**, randomly picked per trial. The selector at
  `multipleStaircase.m` `nextStatus.currentStaircase = ceil(rand *
  length(currentStatus.staircase));`. When detected:
  - `n_interleaved_staircases = length(params.stepStart)` (or equivalent)
  - The keying variable (often orientation / image-class) is the
    factor that interleaves; note it as a within-trial factor.
- Per-trial save for reconstruction (gold standard): the staircase
  struct itself holds `s.response(:)`, `s.strength(:)`, `s.reversals(:)`,
  so saving the struct at end-of-run is sufficient. If the script
  does NOT save it (no `save(..., 'staircase', ...)` call), the
  trajectory cannot be reconstructed → downgrade reproducibility's
  randomization component.

For Bayesian-adaptive engines callable from mgl (e.g. `psybayes` —
Acerbi's Kontsevich-Tyler PSI), detection is by import / call rather
than pattern. See the "Bayesian adaptive engines" subsection of the
PTB lens for the shared rules.

## Common pitfalls

- **Mode-A trial count from `task.parameter` cardinality** — many
  Gardner Lab scripts set `task.numTrials = inf` and let the budget
  emerge from `task.numBlocks × prod(numel(task.parameter.X))`. A
  lens that reads `task.numTrials` literally underestimates by
  orders of magnitude.
- **Mode-B trial count from `length(expBlock.contSeq)`** — the
  schedule is pre-built; trial count is the sequence length, not a
  literal `nT`. Hierarchy counts must read the generator.
- **Factor extraction from `task.thistrial.X` alone is WRONG** — that
  field shows the *current trial's value*, not the factor levels. The
  levels live in `task.parameter.X = [...]` (the assignment) or in
  the generator that built `expBlock.*Seq`.
- **Eye-tracker presence in directory ≠ active eye tracking.** Many
  mgl trees ship `eyeCalib*.m` helpers as framework includes even
  when the canonical entry never invokes them. Check the call graph,
  not file existence.
- **Dated `<name>_YYMMDD.m` files are an evolution chain, not parallel
  experiments.** HJL's `psychExpPdmCds_110622` → ... → `psychExpPdmCds_120520`
  → `psychExp_062512` is one project's monthly snapshots. Treating
  them as independent ≈25x over-counts. Exclude `*~`, `*.svn-base`,
  `*conflicted copy*`, `*orig.m` from canonical-entry consideration;
  prefer the latest-dated authored variant.
- **SVN `*.svn-base` files are NOT separate scripts.** A `Code/`
  directory with 800+ `*.svn-base` siblings is one SVN working copy
  shadow per tracked file. Skip them in the file-count denominators
  and don't analyze them.
- **`task.private` is mgl-valid, not MATLAB OOP-private.** It's a
  user-defined slot for block-level constants recognized by mgl's
  field validator. Don't confuse with `methods (Access = private)`.
- **`getLastStimfile(myscreen)` means cross-run state.** The next
  run's behavior depends on the previous run's saved staircase — note
  in reproducibility, don't pretend each invocation is independent.
- **Replay mode is a feature, not a bug.** `afcom.m` / `afmap.m` style
  `replay=<filename>` arg + `initScreen('replayScreen')` lets the
  experiment re-render offline against a saved stimfile. Recognize
  the arg-parse pattern (`replay=''` default in `getArgs`) and tag
  the script as "replay-mode capable" in reproducibility notes
  (this is a strong positive signal).

## Canonical entry-point picker

When multiple mgl scripts coexist in one directory:

1. Skip `taskTemplate*.m`, `taskTemplateStaircase.m` etc. — those are
   **framework templates** Gardner ships as starting points, NOT
   experiments. Even when present in HJL's `Code/`, they're library
   includes, not entries.
2. Skip files matching `*~`, `*.svn-base`, `*conflicted copy*`,
   `*orig.m`, `*backup*.m`.
3. Among the remaining, prefer the **latest-dated** `<name>_YYMMDD.m`
   or `<name>_YYYYMMDD.m`. Ties broken by absence of conflict suffix.
4. If no dated variant, prefer the file whose `function` line
   returns `myscreen` (mgl-callback canonical) or the file whose
   filename matches the directory's project name (`Main_RingExp/Code/`
   → look for `psychExp*` / `runRingExp*`).
5. Open the file and confirm the canonical loop / `task.parameter`
   block / `mglOpen` call exists. If not, the picked file may itself
   be a helper — re-pick.

## Lens-level scoring hints

- mgl-callback + `task.parameter` + saved stimfile + `getLastStimfile`
  warm-start = mature reproducibility surface (award full
  `environment_capture` + partial `version_pinning` from SVN `$Id$`).
- mgl-primitive + explicit `expData.seedRand` save + `genExpBlock`
  with `mseq` = full `seed` + full `randomization` (deterministic
  m-sequence is reproducible given saved seed).
- mgl framework files (`initTask.m`, `updateTask.m`, etc.) inside the
  code dir → version-pinning bonus if SVN keywords or git submodule
  pin detected, otherwise neutral.
