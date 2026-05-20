# Generic / custom-loop / R / lab.js lens

Use when no dedicated lens matches OR when `platform.framework` is
`custom` / `mixed` / `lab.js` / `r`. Load before Passes 3–7.

## Encoding map

- **Trial unit**: innermost loop iteration (`for i in 1:nT`, `for (let
  i=0; i<n; i++)`, `for (i in 1:N)` in R).
- **Block**: enclosing loop, or one R-script section per block, or a
  `lab.js` `Sequence({content: [...]})` content array length.
- **Session**: usually one per script invocation; multi-session is
  rare in custom code (look for an explicit outer wrapper or repeated
  invocation with a session arg).

### Factors

- Variables that change per loop iteration AND are saved per-iteration.
- Branches: `if (block_kind === 'training')` → `within_session` factor.
- `runif(...)`, `sample(...)`, `np.random.<X>` per trial → `per_trial`,
  `level_source: rng-sampled`.
- A condition table read from CSV / TSV → `level_source:
  conditions-file`.

### Parameters

Convention-driven detection:

- SCREAMING_SNAKE constants (`N_TRIALS`, `ITI_MS`, `FEEDBACK_MS`) →
  `shape: constant`. Pull every one of these into `parameters[]` even
  if used only inside a function — they're typically the timing /
  schedule fundamentals.
- R `<-` and `=` both count as assignment.
- Hard-coded paths (raw strings) → record verbatim in `storage.data_paths`.

### Per-trial saved variables

- Python: `rows.append({...})` then `pd.DataFrame(rows).to_csv(...)`.
  The dict keys are columns → `saved_variables`.
- R: `rbind(results, data.frame(...))` then `write.csv(results, ...)`.
- vanilla JS: `results.push({...})` then a serializer (CSV/JSON).
- lab.js: `Form` component's `responses` keys ship as `saved_variables`.

Sinks:

- Python: `to_csv`, `np.save`, `pickle.dump`, `json.dump`,
  `with open(...) as f: f.write(...)`.
- R: `write.csv`, `write_csv` (readr), `fwrite` (data.table),
  `saveRDS`.
- JS: `fs.writeFileSync`, `fetch(url, {method:'POST', body:...})`,
  `localStorage.setItem`.

### Display

- Python: `matplotlib.pyplot.savefig`, `plt.<plot kind>`,
  `seaborn.<plot>`, `plotnine.ggsave`.
- R: `ggsave`, `pdf()/dev.off()`, `png()/dev.off()`.
- JS: `chart.js` calls, `d3` selections, raw canvas — log only if a
  *save* path is reached.

### Reproducibility hooks

- Seed:
  - Python: `random.seed(s)`, `np.random.seed(s)`,
    `torch.manual_seed(s)` (if torch is imported for some reason).
  - R: `set.seed(s)`. Pinned source if `s` is a literal int or a
    derivation from subject ID.
  - JS: `seedrandom`, `chance.js` with `new Chance(seed)`.
- Randomization: scheme depends on the package. Pure
  `Math.random()` / `runif()` without a seed pinning → `unpinned`.
- Version pinning:
  - Python: `requirements.txt` + `pip freeze > requirements.lock` or
    Poetry/Hatch lock, or Conda `environment.yml` + `conda-lock`.
  - R: `renv.lock`, `packrat/packrat.lock`.
  - JS: `package-lock.json`, `yarn.lock`, `pnpm-lock.yaml`.
- Environment capture:
  - A Dockerfile bumps `completeness` to at least `partial`.
  - `nix.lock` / `flake.lock` → `full`.

### Common pitfalls

- Skipping per-trial variables because they're "obvious" — list every
  column in the output CSV.
- Confusing iteration counts (`n_trials`) with factor levels.
- Treating a function-local literal as the entire parameter set — pull
  module-level constants too.
- R scripts that load conditions from a `.RData` file: `load("cb.RData")`
  pulls a counterbalancing scheme; record in `design_matrix_summary`
  and add an `open_question` if the data file isn't available.
