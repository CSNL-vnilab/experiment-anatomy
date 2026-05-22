# PsychoPy / PsychoJS lens

Use when `platform.framework == "psychopy"` (desktop Python) OR
`platform.framework == "psychojs"` (web export). Load before Passes 3–7.

PsychoPy ships two runtimes that share design but differ in execution:

- **Coder / Builder-desktop** — `.py` script, `from psychopy import …`,
  runs locally against a `visual.Window`. Treat as Python under the
  rules in §1–§4.
- **PsychoJS Builder export** — `.psyexp` (XML source) + `<name>.js`
  (auto-generated 4 000–8 000-line runtime) + `index.html` (+
  `<name>-legacy-browsers.js` IIFE fallback), runs in a browser via
  PsychoPy's PsychoJS port. Treat with §5 ("PsychoJS Builder export
  subsection") — the rules below in §1–§4 still apply for factor /
  hierarchy / data-capture *semantics*, but the file shape and the
  bind-to-xlsx mechanism differ.

## 1. Encoding map (coder / desktop)

- **Trial structure**: `data.TrialHandler(trialList=…, nReps=N)` —
  trial count = `N × len(trialList)`. `MultiStairHandler`, `TrialHandlerExt`,
  `StairHandler` are equivalent for counting purposes.
- **Block structure**: outer `for loop` enclosing the TrialHandler iterator,
  or multiple handler instantiations in sequence.
- **Session**: `expInfo['session']` filled via `gui.DlgFromDict` at start.

## 2. Factors (coder)

- `data.importConditions('cond.csv')` → `level_source: conditions-file`.
  The factor itself is each column name; the levels live in the CSV
  (you can NOT enumerate them from code — note this).
- `expInfo['cond']` referenced in `if expInfo['cond'] == ...` → factor.
- Code reading `thisTrial['col']` — `col` is a within-session factor
  (a column of the conditions table).
- Counterbalance via `data.importConditions(file, selection=...)`
  where `selection` depends on subject → record in
  `design_matrix_summary`.

## 3. Per-trial saved variables (coder)

- `.addData('name', value)` — every call ships one column to the data
  file. Category: usually `response`/`timing`.
- `thisExp.addData(...)` — same, with `thisExp` being the
  `ExperimentHandler`.
- `<handler>.data` columns auto-populated by `core.Clock` /
  `event.waitKeys` (RT, keys, frame-rate).

Sink:

- `thisExp.saveAsWideText('x.csv')` / `.saveAsPickle('x.psydat')`.
- `logging.LogFile` with level set → log file.

## 4. Display / reproducibility (coder)

- Participant: `visual.Window`, `visual.<Stim>`, `<stim>.draw()`,
  `win.flip()`, `event.waitKeys`. `core.wait(t)` blocks for timing.
- Experimenter figures: `matplotlib.pyplot.savefig`, `plt.plot`,
  `plt.imshow`, `plt.bar`. Builder export rarely produces these; custom
  Coder scripts often do.
- Seed: `numpy.random.seed`, `random.seed`, PsychoPy's
  `data.functions.shuffle(*, seed=)`. Note if seed comes from
  `expInfo['participant']` (deterministic) vs `time.time()`.
- Environment capture: `requirements.txt`, `environment.yml`,
  `pyproject.toml` + `poetry.lock`, `psychopyVersion` written into the
  data file. Builder writes `_psychoPyVersion` automatically — count
  that as `partial` if no requirements file.

## 5. PsychoJS Builder export subsection

### 5.1 Detection — the four-file fingerprint

A Builder export emits **four** sibling files in the same directory.
Require **all four** before classifying as `psychojs-builder`:

- `<name>.psyexp` — XML source (PsychoPy Builder's editable form)
- `<name>.js` — auto-generated ES module runtime (typically 4 000–
  8 000 lines)
- `<name>-legacy-browsers.js` — auto-generated IIFE fallback for
  browsers without ES-module support
- `index.html` — web entry; `<title>` literally ends with `[PsychoPy]`

**Hand-written PsychoJS apps can ship `.psyexp` + `.js` + `.html`
side-by-side without being Builder exports.** The four-file presence
is NECESSARY but NOT SUFFICIENT. To confirm Builder, additionally
require **at least 3 of the following Scheduler-graph signals** (these
are what the Builder *generates* — hand-written PsychoJS doesn't
adopt this scaffold):

- `const flowScheduler = new Scheduler(psychoJS);` followed by a
  literal cascade of `flowScheduler.add(<routineName>RoutineBegin);`
  / `.add(<routineName>RoutineEachFrame);` / `.add(<routineName>RoutineEnd);`
  calls.
- A function named `<routine>RoutineBegin(snapshot)` whose body
  starts with the Builder boilerplate `<routine>Clock.reset();
  routineTimer.reset(); routineTimer.add(<literal>); frameN = -1;
  continueRoutine = true; routineForceEnded = false;`.
- The conditional advance pattern at end of `<r>RoutineEnd`:
  `if (currentLoop === psychoJS.experiment) { psychoJS.experiment.
  nextEntry(snapshot); }`.
- Component telemetry auto-emit pairs: `psychoJS.experiment.addData(
  '<routine>.started', globalClock.getTime());` AND a matching
  `addData('<routine>.stopped', ...)` in End.

If only ≤2 of those Scheduler-graph signals fire (even with the
four-file fingerprint present), classify as
`platform.framework = "psychojs-handwritten"`, NOT `psychojs-builder`.
The lens still applies the .psyexp-as-source rules but skips the
auto-telemetry-vs-researcher-column separation.

Inside `<name>.js`, hard signals (require ≥4):

- `import { core, data, sound, util, visual, hardware } from
  './lib/psychojs-<ver>.js';` (versioned filename, relative `./lib/`)
- `const { PsychoJS } = core; const { TrialHandler, MultiStairHandler }
  = data; const { Scheduler } = util;` (verbatim Builder destructure)
- `let expName = '<name>';  // from the Builder filename that created
  this script` (Builder's literal comment)
- `const psychoJS = new PsychoJS({ debug: true });`
- `psychoJS.openWindow({ ... units: 'height', ... });`
- `const flowScheduler = new Scheduler(psychoJS);` (top of `run()`)
- Function-body returns `Scheduler.Event.NEXT`
- `psychoJS.experiment.addData(...)` (anywhere)
- Routine triple by name: `<routine>RoutineBegin(snapshot)`,
  `<routine>RoutineEachFrame()`, `<routine>RoutineEnd(snapshot)`
- Loop function triple: `<loop>LoopBegin`, `<loop>LoopEnd`,
  `<loop>LoopEndIteration`
- `expInfo['psychopyVersion'] = '<x.y.z>';` — version is baked in

Negative signals that rule OUT Builder:

- `import { initJsPsych }` — that's jsPsych.
- `class <X> extends ...` with hand-organized trial / block classes —
  hand-written PsychoJS.
- Webpack / Vite minified bundle output (`(()=>{var ...})()`) — not
  Builder.
- Absence of the `psychoJS.experiment.nextEntry(snapshot)` idiom.

### 5.2 Scheduler / flowScheduler / loopScheduler abstraction

The execution model is a Scheduler graph, NOT a top-down `for` loop:

```
flowScheduler.add(updateInfo);
flowScheduler.add(experimentInit);
const <loop>LoopScheduler = new Scheduler(psychoJS);
flowScheduler.add(<loop>LoopBegin(<loop>LoopScheduler));
flowScheduler.add(<loop>LoopScheduler);
flowScheduler.add(<loop>LoopEnd);
flowScheduler.add(quitPsychoJS, '', true);
```

Each `<loop>` is one TrialHandler scope. Loops nest by calling
`flowScheduler.add(<innerLoop>LoopBegin(<innerLoop>LoopScheduler))`
inside an outer routine body. Trial count is the **product** of all
nested `nReps` × the rows of each loop's xlsx.

For each loop scope, extract:

- `nReps` — can be a literal (`nReps: 6`) OR a JS identifier
  (`nReps: nrep_block_test`). When it's an identifier, trace it back
  through `importConditions(snapshot)` to the parent loop's xlsx
  column — Builder injects xlsx column names as iteration-local
  variables.
- `method: TrialHandler.Method.{RANDOM | SEQUENTIAL | FULL_RANDOM}` —
  default `RANDOM` for Builder.
- `seed: <value>` — almost always `undefined` (Builder default; PsychoJS
  falls back to `Math.random()`, **unseeded**). Record as a
  reproducibility weakness.
- `trialList: '<file>.xlsx'` OR `trialList: undefined`. The latter
  means the loop iterates `nReps` times with no condition rows — the
  schedule lives elsewhere (often in a parent loop's xlsx OR in
  hand-written `TrialHandler.importConditions` outside any `new
  TrialHandler({})`).

### 5.3 Resource files (xlsx / csv) — the real factor source

Builder lists every resource explicitly:

```js
psychoJS.start({
  expName, expInfo,
  resources: [
    {'name': 'session_loop.xlsx', 'path': 'session_loop.xlsx'},
    {'name': 'trial_general_main.xlsx', 'path': 'trial_general_main.xlsx'},
    {'name': 'images/face_001.png', 'path': 'images/face_001.png'},
    ...
  ]
});
```

For each xlsx referenced in a `trialList:`, you MUST read the xlsx to
enumerate factor levels. Method:

```bash
python3 -c "
import openpyxl
wb = openpyxl.load_workbook('<path>', read_only=True)
ws = wb.active
print('cols:', [c.value for c in ws[1]])
print('rows:', ws.max_row - 1)
for r in ws.iter_rows(min_row=2, max_row=6, values_only=True):
    print(r)
"
```

Fallback when openpyxl is unavailable: `unzip -p <file>
xl/sharedStrings.xml | head -c 4000` and grep for column names.

Apply this typing heuristic per column:

- `nunique == 1` across all rows → **parameter (constant scalar)**, not
  a factor. Lift into `parameters[]` with `shape="constant"`.
- `nunique ≤ 8` AND discrete (int or low-precision float) →
  **categorical factor**. Levels = the unique values.
- `nunique ≥ 10` AND numeric with even spacing → **continuous factor**
  (treat as a design variable, not as discrete levels).
- `nunique == row_count` AND string-like → **stimulus identifier /
  catalog**, not a factor. Emit as `parameters[]` with
  `shape="input"` pointing at the xlsx.
- Sparse-fill (≥50 % None) → **metadata / annotation**, suppress
  unless researcher confirms factor status.
- Two columns in perfect bijection across all rows → collapse to one
  factor (record both names in `factor.aliases[]`); prefer the more
  semantic name. Example: BYL's `ecc_idx` ↔ `ecc_deg`.
- Column name in `{block, run, session, phase}` with equal-count
  partitions → **block tag**, not a design factor.

### 5.4 Config-as-conditions trick

A 1-row xlsx with all columns nunique==1 (e.g. MSY's `session_loop.xlsx`
with 6 columns × 1 row of integer scalars) is **not** a trial schedule —
it's a parameter sidecar that Builder treats as a 1-trial TrialHandler
so its columns become iteration-local variables for downstream nested
loops. Classify as `parameter_sidecar` and lift each column into
`parameters[]`.

### 5.5 Routine triple — Begin / EachFrame / End

Each Routine is three independent functions Builder concatenates:

- `<r>RoutineBegin(snapshot)`: resets `Routine` clock, `frameN = -1`,
  `t = 0`, sets `continueRoutine = true`, `routineForceEnded = false`;
  baked literal `routineTimer.add(<max-dur>)`; per-component
  `<comp>.setText(...)` / `.setImage(...)` / `.reset()` updates;
  researcher's "Begin Routine" code spliced in verbatim; auto-emits
  `psychoJS.experiment.addData('<r>.started', globalClock.getTime())`.
- `<r>RoutineEachFrame()`: `t = <r>Clock.getTime(); frameN++;` then
  per-component `if (t >= <onset> && X.status === NOT_STARTED) { ... }`
  blocks with baked literal onsets; `routineTimer` / `frameRemains`
  drives stop transitions; researcher's "Each Frame" code spliced in.
- `<r>RoutineEnd(snapshot)`: auto-emits `<r>.stopped` + per-component
  `<comp>.response`, `.rt`, `.duration`, `.keys`, `.numClicks` etc.;
  conditional `currentLoop.addResponse(...)` block for MultiStair use;
  `if (currentLoop === psychoJS.experiment) { nextEntry(snapshot); }`.

When emitting structured hierarchy, group the Routine triple as ONE
"routine" node with three sub-phases, not three sibling functions.

### 5.6 Data capture surface

Two layers of `addData` columns ship to the per-subject CSV:

**Auto component telemetry** (Builder writes these unconditionally;
one row per Routine per trial):

- Per Routine: `<routine>.started`, `<routine>.stopped` (globalClock s)
- Slider: `<slider>.response` (= `getRating()`), `<slider>.rt`
  (= `getRT()`)
- Keyboard: `<kb>.keys`, `<kb>.rt`, `<kb>.duration`
- Mouse: `.x`, `.y`, `.leftButton`, `.midButton`, `.rightButton`,
  `.time`, `.clicked_name` (7 cols per Mouse)
- Textbox: `<box>.text`

**Researcher-added columns** (any `psychoJS.experiment.addData("name",
value)` outside the auto-emit blocks): list every site — these are the
analysis-grade columns. Example fingerprint from MSY's cat_mag:
`ses_num, main_ex, cond_order, block, trial, stim_type, stim_num,
stim_ans, stim, resp, rt, ID_input`.

When reporting `saved_variables[]`, separate these two groups with a
note; do NOT inflate `category=response` count with auto-telemetry.

### 5.7 Hand-written shuffle inside Builder export

A non-trivial fraction of Builder exports contain researcher-written
JS in CodeComponents — when CodeComponent count > 5, the JS is no
longer 100 % template. Expect patterns like:

```js
allTrials = TrialHandler.importConditions(psychoJS.serverManager, "x.xlsx");
myCustomList = shuffleWithConstraints(allTrials, 2);  // no >2 consecutive
```

Detection: a `TrialHandler.importConditions(...)` call outside any
`new TrialHandler({...})` constructor signals **hand-written schedule
control**. The Builder TrialHandler in the same loop may have
`trialList: undefined` — it's just spinning the scheduler nReps times
while the real schedule lives in `myCustomList`.

When detected:

- `factor.level_source = "conditions-file (xlsx)"`
- `randomization.scheme = "constrained_shuffle (hand-written)"`
- Quote the shuffle function's constraint (e.g. "no >N consecutive
  same `<col>` value")
- Note that PsychoJS's `Math.random()` is unseeded unless the
  researcher imported `seedrandom`.

### 5.8 Prolific / Pavlovia integration

- `psychoJS.setRedirectUrls('<prolific-completion-url>', '<fail-url>')`
  → Prolific deployment.
- `util.addInfoFromUrl(expInfo)` → URL params (`PROLIFIC_PID`,
  `STUDY_ID`, `SESSION_ID`) merged into `expInfo`. Absence of explicit
  `PROLIFIC_PID` field in the `expInfo` dialog is normal.
- `let PILOTING = util.getUrlParameters().has('__pilotToken');` →
  Pavlovia pilot mode.
- `psychoJS.experiment.dataFileName = ("./" + "data/${pid}_${expName}_${date}");`
  → relative `./data/` storage path; on Pavlovia hosting, this becomes
  the Pavlovia data path.

### 5.9 Reproducibility surface (Builder export)

- RNG: `seed: undefined` in every TrialHandler is the Builder default.
  PsychoJS falls back to `Math.random()`. Score: `pinned=false` unless
  a seeded shuffle library (`seedrandom`, `chance.js`) is imported.
- `util.shuffle` / `util.randint` are PsychoJS's shuffle helpers; their
  output is reproducible only if the JS-global RNG is seeded first.
- `psychopyVersion` baked in `expInfo` is recoverable from the saved
  CSV's `psychopyVersion` column → award `version_pinning = partial`.
- No `requirements.txt` / lockfile in a Builder export by default — the
  PsychoJS `<ver>` is the only pin. If `./lib/psychojs-<ver>.js` is
  shipped alongside (rare; Pavlovia provides at deploy), upgrade pin
  to `full-for-runtime`.

### 5.10 .psyexp XML — supplementary structure

The `.psyexp` is a more reliable source for **factor structure** than
the .js (the JS bakes the structure into Schedulers; the XML carries
explicit `<LoopInitiator>` and `<Param name="conditionsFile">` nodes).
When extracting hierarchy:

- Parse `<LoopInitiator loopType="TrialHandler">` blocks; their
  `conditionsFile` parameter is the xlsx binding.
- Inline `conditions=[{key:val,...}]` mirror inside `<LoopInitiator>`
  for single-row xlsx (Builder duplicates the row as a Python-dict
  literal — useful when the xlsx is binary).
- Component types and counts (`<TextComponent>`, `<SliderComponent>`,
  `<MouseComponent>`, `<CodeComponent>`) are visible at the
  `<Routines>` level; `CodeComponent` count is a complexity signal
  (high → much hand-written JS; low → near-pure template).

When emitting hierarchy, trust the .psyexp over the .js for nested
loop topology; trust the .js for runtime side effects / data capture.

## Common pitfalls (covers both runtimes)

- Forgetting that conditions.csv / .xlsx columns are factors — you see
  the factor *name* in code (`thisTrial['contrast']`) but never the
  levels list. Add an `open_question` asking the researcher to attach
  the CSV / .xlsx file if you can't read it.
- Mixing `expInfo['session']` (a metadata string) with a real
  `within_subject` axis. If the script branches on it, it's a factor;
  if it's only saved, it's `subject_meta`.
- Builder-exported scripts have a lot of auto-generated noise
  (`thisComponent.tStart = ...`, tautological `typeof 'space' ===
  'string' ? ['space'] : 'space'` guards) — that's NOT researcher
  IV/parameter data and should not be critiqued for style.
- The Routine triple isn't a class hierarchy — it's three separately-
  defined functions Builder concatenated. Don't infer OOP.
- `_e_1` / `_m_1` / `_e_2` suffixes on Builder component names are
  Builder's component-renaming when the researcher duplicated a
  Routine. Treat as parallel streams (e.g. exercise vs main), not as
  researcher confusion.
- `nReps` resolves through `importConditions(snapshot)` — total trial
  counts cannot be read off the .js alone when nReps is an identifier.
  Surface the resolution chain explicitly.
- An xlsx with row_count == 1 and every column nunique == 1 is a
  **parameter sidecar**, not a 6-factor × 1-level design.
- `trialList: undefined` inside a `new TrialHandler({...})` is the
  Builder fingerprint for "schedule lives elsewhere"; do not record
  the loop as empty.
- A repo with `<name>.py` + `<name>.js` + `<name>.psyexp` is a Builder
  project that exports to both runtimes. The `.py` is the desktop
  twin of the `.js`; analyzing either alone misses cross-platform
  behavior. Prefer the `.psyexp` as the structural ground truth and
  cite both runtimes in `platform.runtimes[]`.
