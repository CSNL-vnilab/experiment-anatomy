# Rigor + reproducibility checklist

Pass-10 (reproducibility) and Pass-11 (rigor) both score 0–100 with
weighted components. This document is the source of truth for those
weights and what evidence each component needs.

## Reproducibility — could a stranger reproduce these numbers?

| Component | Max | What it asks | Strong evidence | Weak evidence | None |
|-----------|----:|---|---|---|---|
| **Seed pinned** | 25 | Is the RNG state deterministic per subject? | `rng(subjNum)`, `np.random.seed(subjNum*day)`, `set.seed(subj_id)` — derived from subject identifier | `rng(123)` constant for all subjects, OR `rng('shuffle')` with the resulting seed *recorded* to disk | unset, `rng('shuffle')` not recorded |
| **Randomization** | 15 | Is the scheme declared and matches the code? | `latin_square`, `counterbalanced` scheme with mapping in design_matrix_summary AND visible in code | `block_shuffle` / `trial_shuffle` with package defaults | `none` / `ad_hoc` / `unknown` |
| **Version pinning** | 25 | Are dependency versions pinned? | A lock file present (`pip freeze`, `poetry.lock`, `package-lock.json`, `renv.lock`, `Manifest.toml`) | requirements.txt / package.json with floating versions (>=, ^, ~) | nothing — pure code, no manifest |
| **Environment capture** | 20 | Can the runtime be recreated? | Lockfile + Dockerfile/nix flake = `full` | requirements.txt/environment.yml alone = `partial` | nothing = `absent` |
| **Deterministic paths** | 15 | Do data sinks use deterministic naming? | All paths contain `<subID>` / `<date>` / iteration counters; no hardcoded `/Users/<name>` outside config | mix of patterns + a few absolutes | every path is hardcoded absolute |

Compute the score by summing components. Cap at 100.

Notes:
- A score of 75+ does NOT mean the experiment is reproducible — it means
  the *code-level* signals are there. Field reproducibility depends on
  data availability, instructions, hardware, etc.
- A score of <40 should always be accompanied by a `note` in
  `reproducibility.score.notes` explaining the biggest gaps.

## Rigor — methodological practice visible from code+docs

| Component | Max | What it asks | Evidence required |
|-----------|----:|---|---|
| **Counterbalancing** | 25 | Are IVs counterbalanced across subjects? | Scheme described in design_matrix_summary; code branches symmetrically by subject ID |
| **Sample size justification** | 20 | Is N defended? | `power_analysis` with numbers in docs OR `precedent` with citation; `ad_hoc` is partial credit |
| **Blinding** | 15 | If applicable, are experimenter/participant blinded? | Code shows blinded labels (`A`/`B` instead of `treatment`/`control`); docs note it |
| **Pre-registration marker** | 10 | OSF / AsPredicted URL or ID in docs? | A URL or ID string |
| **Exclusion rules** | 15 | Are trial/subject exclusion rules declared? | Code AND docs declare them (RT cutoff, accuracy floor, missing response) |
| **Static checks pass** | 15 | All 5 boolean checks pass | every_factor_has_role, no_single_value_factor, saved_5_categories_present, hierarchy_complete, no_dead_branches_in_conditions |

Static checks (binary, all must be evidence-backed):

- **every_factor_has_role**: ∀ f ∈ factors, f.role != "unknown".
- **no_single_value_factor**: ∀ f ∈ factors, len(f.levels) > 1 OR f.level_source ∈ {`rng-sampled`, `adaptive`, `conditions-file`, `inline-literal` and the level set is *defined elsewhere* (e.g. inside a pre-generated schedule .mat) — describe that in `description`}.
- **saved_5_categories_present**: each of {stimulus, response, timing, block_summary, session_meta} has ≥ 1 entry — UNLESS the paradigm legitimately lacks one (e.g. a survey has no per-trial timing channel — flag in `open_questions` instead).
- **hierarchy_complete**: hierarchy.one_liner is non-null AND
  `n_blocks * n_trials_per_block` (or the phase sum) is ≥ total_trials_estimate / 1.5. If any count is `null`, this check is `false` AND a topic=`hierarchy` `open_question` MUST be queued (no silent null).
- **no_dead_branches_in_conditions**: conditions[] only lists factor-level combos that the code branches into (use `applies_when` evidence).
- **schedule_consistency** (only evaluated when the PTB pre-generated schedule pattern is active — see `prompts/lenses/psychtoolbox.md` § "Pre-generated schedule pattern"): the literal block/trial constants in the entry/setup AGREE with the schedule cell-array dimensions (`length(par.schedule.Stm)` × `length(par.schedule.Stm{1})`). If they disagree, this check is `false` and the mismatch must appear in a topic=`hierarchy` `open_question`. If the pattern isn't active, the check is `true` by default (vacuously).

## Sanity checks before scoring

Before computing scores, validate the spec itself:

- factors[] is non-empty for any experiment with > 1 trial unless it's
  a pure observation paradigm — if 0 factors, add an open_question
  asking the researcher to confirm "design without IV" is intentional.
- saved_variables[] non-empty.
- parameters[] usually non-empty (a 1-trial demo can have 0).
- hierarchy.sessions[0].phases[0].n_trials_per_block matches the trial
  count anywhere visible in saved_variables sinks (CSV header / mat
  size hint).

Score `0` for a component is fine — better to report low and accurate
than inflate.
