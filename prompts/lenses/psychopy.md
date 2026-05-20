# PsychoPy / Python lens

Use when `platform.framework == "psychopy"`. Load before Passes 3–7.

## Encoding map

- **Trial structure**: `data.TrialHandler(trialList=…, nReps=N)` —
  trial count = `N × len(trialList)`. `MultiStairHandler`, `TrialHandlerExt`,
  `StairHandler` are equivalent for counting purposes.
- **Block structure**: outer `for loop` enclosing the TrialHandler iterator,
  or multiple handler instantiations in sequence.
- **Session**: `expInfo['session']` filled via `gui.DlgFromDict` at start.

### Factors

- `data.importConditions('cond.csv')` → `level_source: conditions-file`.
  The factor itself is each column name; the levels live in the CSV
  (you can NOT enumerate them from code — note this).
- `expInfo['cond']` referenced in `if expInfo['cond'] == ...` → factor.
- Code reading `thisTrial['col']` — `col` is a within-session factor
  (a column of the conditions table).
- Counterbalance via `data.importConditions(file, selection=...)`
  where `selection` depends on subject → record in
  `design_matrix_summary`.

### Per-trial saved variables

- `.addData('name', value)` — every call ships one column to the data
  file. Category: usually `response`/`timing`.
- `thisExp.addData(...)` — same, with `thisExp` being the
  `ExperimentHandler`.
- `<handler>.data` columns auto-populated by `core.Clock` /
  `event.waitKeys` (RT, keys, frame-rate).

Sink:

- `thisExp.saveAsWideText('x.csv')` / `.saveAsPickle('x.psydat')`.
- `logging.LogFile` with level set → log file.

### Display

- Participant: `visual.Window`, `visual.<Stim>`, `<stim>.draw()`,
  `win.flip()`, `event.waitKeys`. `core.wait(t)` blocks for timing.
- Experimenter figures: `matplotlib.pyplot.savefig`, `plt.plot`,
  `plt.imshow`, `plt.bar`. Builder export rarely produces these; custom
  Coder scripts often do.

### Reproducibility hooks

- Seed: `numpy.random.seed`, `random.seed`, PsychoPy's
  `data.functions.shuffle(*, seed=)`. Note if seed comes from
  `expInfo['participant']` (deterministic) vs `time.time()`.
- Environment capture: `requirements.txt`, `environment.yml`,
  `pyproject.toml` + `poetry.lock`, `psychopyVersion` written into the
  data file. Builder writes `_psychoPyVersion` automatically — count
  that as `partial` if no requirements file.
- `data.ExperimentHandler` writes its `runtimeInfo` block — capture
  presence/absence in `environment_capture.files_found`.

### Common pitfalls

- Forgetting that conditions.csv columns are factors — you see the
  factor *name* in code (`thisTrial['contrast']`) but never the levels
  list. Add an `open_question` asking the researcher to attach the CSV.
- Mixing `expInfo['session']` (a metadata string) with a real
  `within_subject` axis. If the script branches on it, it's a factor;
  if it's only saved, it's `subject_meta`.
- Builder-exported scripts have a lot of auto-generated noise
  (`thisComponent.tStart = ...`) — that's NOT user IV/parameter data.
