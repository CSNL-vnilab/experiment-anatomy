# jsPsych / JavaScript lens

Use when `platform.framework == "jspsych"`. Load before Passes 3–7.

## Encoding map

- **Trial unit**: each node in the `timeline` array. Plugin type
  (`type: jsPsychHtmlKeyboardResponse`, `jsPsychImageButtonResponse`, …)
  determines the trial flavor.
- **Block**: a sub-timeline pushed into the master timeline; or
  `repetitions` / `sample` on a node.
- **Session**: usually single-session unless a custom outer loop wraps
  `jsPsych.run()` multiple times.

### Factors

- `jsPsych.randomization.factorial({a:[...], b:[...]}, reps)` — keys are
  factors; arrays are levels.
- `timeline_variables: [{a:..., b:...}, ...]` with
  `jsPsych.timelineVariable('x')` — `x` is a `within_session` factor.
- `repetitions: N` on a timeline node — that's just count, not a factor.
- `randomize_order: true` on a sub-timeline — a randomization scheme,
  not a factor itself.

### Per-trial saved variables

Three sources, all category `response` / `stimulus` / `timing`:

1. **Node-attached metadata**: `data: { condition: 'A', stim_id: 17 }`
   on a trial node — every column there ships per-trial.
2. **on_finish callback**: `on_finish: function(data) { data.computed_x = ...; }`
   adds a column.
3. **Global metadata**: `jsPsych.data.addProperties({ subject: 's01' })`
   adds the same columns to EVERY row.

Plugin defaults: `rt`, `response`, `stimulus`, `trial_type` ship by
default — list them in `saved_variables` even if not explicitly added.

Sinks:

- `jsPsych.data.get().csv()` / `.json()` — return data as text.
- `jsPsych.data.get().localSave('csv', 'fname.csv')` — write to disk
  (Electron / Cog only).
- `jsPsychPipe` plugin — write to DataPipe (OSF).
- Custom `saveData(...)` POST to a server endpoint — capture URL.

### Display

- Participant: every plugin's `stimulus` parameter defines what's drawn.
  HTML / image / canvas / video.
- Experimenter figures: rare in pure jsPsych; if `jsPsych.data.get().displayData()`
  is called the result is a debug view, not a saved figure. If a
  separate plotting library (`chart.js`, `d3`) is imported, that's a
  display sink — but check whether the output is saved or just shown.

### Reproducibility hooks

- Seed: jsPsych RNG is `Math.random` by default — NOT seedable without
  a custom RNG. Score: 0 unless a seedable library (`seedrandom`,
  `chance.js` with seed) is imported AND used.
- Randomization: `jsPsych.randomization.shuffle`, `factorial(repetitions, true)`,
  `repeat(stim, n, true)`. Each is non-seedable by default.
- Environment capture: `package.json` + lock file is the gold standard.
  `package.json` without lock → `partial`. No package.json → `absent`.

### Common pitfalls

- Counting `repetitions:` as a factor (it's just a count).
- Missing the plugin's default saved columns (`rt`, `response`,
  `trial_type`).
- `jsPsych.timelineVariable` inside a `data: {}` block — looks like a
  saved variable but it's actually the FACTOR being recorded per
  trial. Count once in `factors`, once in `saved_variables` (it's both).
- Online experiments hosted via Pavlovia / Cognition.run / a custom
  server: the saved data flows OUT of the participant's browser. Note
  the destination as `sink`.
