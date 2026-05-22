# 출력 JSON 각 필드 한국어 해설

`experiment-spec.json` 은 [`schemas/experiment-spec.schema.json`](../schemas/experiment-spec.schema.json)
(JSON Schema 2020-12) 에 정확히 맞춰 출력됩니다. 모든 필드의 의미와
채우는 규칙을 여기에 풀어놓습니다.

## 최상위 구조

```json
{
  "schema_version": "1.1.0",
  "identity":           { ... },
  "platform":           { ... },
  "hierarchy":          { ... },
  "factors":            [ ... ],
  "conditions":         [ ... ],
  "design_matrix_summary": "...",
  "parameters":         [ ... ],
  "saved_variables":    [ ... ],
  "display":            { ... },
  "storage":            { ... },
  "reproducibility":    { ... },
  "rigor":              { ... },
  "adaptive_procedure": { ... } | null,
  "open_questions":     [ ... ],
  "provenance":         { ... }
}
```

`additionalProperties: false` 가 모든 객체에 걸려 있어 — 위에 없는
key 가 들어가면 validation 실패합니다.

---

## `schema_version`

- 항상 문자열. v0.2.0 플러그인은 `"1.1.0"` 을 출력하고, 이전 `"1.0.0"` spec 도 그대로 받아들입니다.
- consumer (PostgreSQL upserter 등) 가 이 값으로 gate 합니다 — major bump 시 consumer 측 가드 코드도 함께 갱신.

## `identity` — 정체성

```json
"identity": {
  "title": "Time2Dist Experiment 2",
  "short_id": "TimeExp2",
  "version": "git:9a1f3e2",
  "summary": "참가자는 두 시간 간격을 비교하여 길이를 판단한다. 5일에 걸쳐 short/long distribution 이 within-subject 로 counterbalance된다.",
  "research_question": "Bayesian observer 모델이 prior 분포의 모양에 따라 어떻게 RT/accuracy 를 예측하는가?",
  "paradigm_genre": "estimation"
}
```

| 필드 | 의미 | 채우는 방식 |
|---|---|---|
| `title` | 풀 제목 | docs 의 첫 H1 / README 첫 줄 / entry 파일 헤더 코멘트에서 추출. 없으면 entry 파일명으로 propose. |
| `short_id` | DB 자연 키 (3–12자 slug) | 인자로 받거나 인터뷰에서 묻기. **researcher 가 정함** — 추측 금지. |
| `version` | 연구자 버전 라벨 / git short SHA | `git rev-parse --short HEAD` 또는 docs 의 "v2.3" 같은 문구. 없으면 null. |
| `summary` | 2–4문장 한국어 요약 | anatomist 가 직접 작성. 무엇을 측정하는지 + 어떤 paradigm 인지. |
| `research_question` | 가설 / 주 DV | README/docs 에서 추출. 없으면 null. |
| `paradigm_genre` | 장르 enum | `psychophysics`, `estimation`, `decision`, `retrieval`, `search`, `perception`, `memory`, `motor`, `categorization`, `attention`, `imagery`, `language`, `social`, `gamified`, `other` 중. |

## `platform` — 플랫폼

```json
"platform": {
  "framework": "psychojs-builder",
  "variant": null,
  "language": "javascript",
  "runtimes": ["python-desktop", "javascript-web"],
  "external_host": null,
  "framework_version": "PsychoPy 2025.2.3 (baked in JS)",
  "language_runtime": "Node 22 (Pavlovia hosting)",
  "external_dependencies": [
    {"name": "psychojs", "version": "2025.2.3", "pinned": true}
  ],
  "detection_confidence": 0.95
}
```

| 필드 | 의미 | 채우는 방식 |
|---|---|---|
| `framework` | 14-value enum | `psychtoolbox`, `psychopy`, `psychojs`, `psychojs-builder`, `psychojs-handwritten`, `mgl`, `jspsych`, `lab.js`, `opensesame`, `neurobs-presentation`, `external`, `custom`, `mixed`, `unknown` |
| `variant` | 서브모드 | mgl 의 `mgl-callback` / `mgl-primitive` / `mgl-hybrid`, Brainard 의 `BrainardLabToolbox`, Gold 의 `snow-dots`, Pelli 의 `pelli-many-runners` 등. 없으면 null. |
| `language` | 주 언어 | matlab / python / javascript / typescript / r / c / cpp / other |
| `runtimes[]` | dual-export 시 | PsychoPy Builder 의 .psyexp + .py + .js triplet 처럼 한 source 가 여러 런타임을 emit 하는 경우. enum: `python-desktop`, `javascript-web`, `matlab-desktop`, `matlab-fmri`, `r-desktop`, `other` |
| `external_host` | framework=external 일 때만 | `{ kind: pavlovia/gorilla/osf/github-elsewhere/lab-private/..., url: string, evidence: string }`. 그 외엔 null. |
| `framework_version` | 프레임워크 버전 | Builder 의 `expInfo['psychopyVersion']`, PTB 의 `Screen('Version')`, mgl 의 SVN `$Id$` 키워드 등. |
| `language_runtime` | 언어 런타임 | `MATLAB R2023b`, `Python 3.11`, `Node 22` 등. |
| `external_dependencies[]` | deps 목록 | `requirements.txt` / `package.json` / `.lock` 파일에서 추출. 각 항목 `{name, version, pinned}`. |
| `detection_confidence` | 0–1 | ≥4 hard signal 동시 발화 → ≥0.9. 2–3 → 0.7–0.9. <0.7 → 자동으로 `platform`-topic open_question 추가. |

## `hierarchy` — session → block → trial

```json
"hierarchy": {
  "one_liner": "session: par.day 1..5 (within_subject); block: for iR=1:nBlocks (12); trial: for iT=1:nT (40)",
  "n_sessions": 5,
  "sessions": [
    {
      "index": 1,
      "label": "Day 1 — practice + threshold estimation",
      "day_range": "1",
      "phases": [
        {"kind": "practice", "n_blocks": 2, "n_trials_per_block": 20, "description": "..."},
        {"kind": "stair",    "n_blocks": 4, "n_trials_per_block": 30, "description": "..."}
      ]
    },
    { "index": 2, "label": "Day 2 — main (dist=A)", "day_range": "2-5", "phases": [...] }
  ],
  "total_trials_estimate": 2400,
  "estimated_duration_min": 90
}
```

| 필드 | 의미 |
|---|---|
| `one_liner` | 한 줄 자유 텍스트로 loop variables + counts + index mapping. 사람이 가장 먼저 읽는 줄. |
| `n_sessions` | 1 이면 single-session (e.g. PsychoJS Builder online). |
| `sessions[].phases[]` | 한 session 안에서 mode 가 바뀌면 phase 로 split. `kind ∈ {training, practice, stair, main, test, transfer, rest, demo, other}`. n_blocks·n_trials_per_block 은 literal 에서 읽거나 null + open_question. **절대 추측 안 함** (Hard rule 2). |
| `total_trials_estimate` | 모든 session × phase 의 합. null 가능. |
| `estimated_duration_min` | 추정 시간 (분). null 가능. |

**Pre-generated schedule (SCHEDULE_ACTIVE) 활성 시**: literal 이 우선, schedule `.mat` 의 cell-array 차원이 sanity check. 불일치 시 `rigor.checks.schedule_consistency = false` + open_question.

## `factors[]` — 조작변수

```json
"factors": [
  {
    "name": "dist",
    "display_name": "Time distribution",
    "type": "categorical",
    "levels": ["short", "long"],
    "level_source": "inline-literal",
    "role": "within_subject",
    "description": "각 참가자가 5일 중 short 분포 2일 + long 분포 2일을 경험. counterbalance 는 make_trial_schedule_duration.m 의 (subj, day) 매핑에 따라.",
    "evidence": ["make_trial_schedule_duration.m:18", "main_duration.m:60"]
  }
]
```

| 필드 | 의미 |
|---|---|
| `name` | 코드에 등장하는 이름 그대로 |
| `display_name` | 사람-읽기용 이름. null 가능. |
| `type` | `categorical`, `continuous`, `ordinal` |
| `levels[]` | 실제 레벨. categorical 은 모든 값 나열, continuous 는 범위·step 정보. adaptive 면 빈 배열. |
| `level_source` | `inline-literal` (코드/.mat에서 읽음) / `conditions-file` (xlsx·csv 결합) / `rng-sampled` (run-time random) / `adaptive` (staircase·Quest·Bayesian) / `inferred` (data 만 보고) / `unknown` |
| `role` | `between_subject` (subjNum/group 으로 분기) / `within_subject` (day/session 으로) / `within_session` (block-kind 로) / `per_trial` (trial-to-trial) / `derived` (IV 가 아님 — confirm-and-drop marker) / `unknown` |
| `evidence[]` | file:line 또는 `interview: <hash>` |

**Derived 는 IV 아닙니다.** 코드에 보이지만 실제로는 다른 변수의 deterministic 함수일 때 — 연구자에게 confirm 받고 drop 하기 위한 marker.

**levels.length ≤ 1** 인 factor 는 거의 상수 — 자동으로 `open_question` 으로 들어갑니다.

## `conditions[]` — 실제 실행된 조합

```json
"conditions": [
  {
    "label": "short-day2",
    "factor_assignments": {"dist": "short", "day": 2},
    "description": "Day 2 에 short dist 그룹에 할당된 trial 들"
  }
]
```

- factor 의 Cartesian product 가 아닌, **코드가 실제로 실행하는 조합만**.
- Counterbalance scheme (Latin square, between-subject group assignment 등) 은 conditions 가 아닌 `design_matrix_summary` (자유 텍스트) 에.

## `design_matrix_summary`

자유 텍스트 (≤4000자). 예시:

```
"subjNum mod 4 → 4개 cohort:
  cohort 0: Day2=A, Day3=B, Day4=B, Day5=A (AB-BA)
  cohort 1: Day2=A, Day3=B, Day4=A, Day5=B (AB-AB)
  cohort 2: Day2=B, Day3=A, Day4=A, Day5=B (BA-AB)
  cohort 3: Day2=B, Day3=A, Day4=B, Day5=A (BA-BA)
Source: make_trial_schedule_duration.m:35-50"
```

Pre-generated schedule 패턴 활성 시 — **반드시 generator 소스에서 verbatim 으로 읽고**, generator 가 번들에 없으면 null + open_question.

## `parameters[]` — setup 상수

```json
"parameters": [
  {
    "name": "tprecue",
    "value": "[0.3 0.5]",
    "type": "array",
    "unit": "seconds",
    "shape": "vector",
    "description": "Pre-cue interval — block 마다 다름",
    "evidence": ["main_duration.m:18"]
  }
]
```

| `shape` | 의미 |
|---|---|
| `constant` | 모든 trial 에 동일한 단일 literal |
| `vector` | 블록마다 변하는 array — block-kind candidate (factor 일 수도) |
| `expression` | 다른 parameter 에서 계산 (`tpost = tprecue + 0.2`) |
| `input` | runtime input (GUI dialog, env var, CLI arg, 또는 loaded xlsx/.mat) |
| `unknown` | 분류 불가 |

## `saved_variables[]` — 출력 데이터

```json
"saved_variables": [
  {
    "name": "par.tp.vbl_resp",
    "scale": "per_trial",
    "category": "timing",
    "format": "array",
    "unit": "seconds",
    "sink": "subID_dayN_main.mat",
    "description": "참가자 응답 시점의 VBL timestamp",
    "evidence": ["main_duration.m:120"]
  }
]
```

5 scale × 9 category 격자에 배치:

| `scale` | 의미 |
|---|---|
| `per_trial` | trial 마다 한 entry |
| `per_block` | 블록 끝에 summary 한 entry |
| `per_session` | session 마다 한 entry (meta, rng_state 등) |
| `per_subject` | 한 참가자 전체에 한 entry (consent, demographics) |
| `global` | session 무관 (log 파일, env capture 등) |

| `category` | 예시 |
|---|---|
| `stimulus` | par.stim.dir, par.kin.speed |
| `response` | par.results.choice, par.results.rt |
| `timing` | par.tp.vbl_*, par.tp.t_resp |
| `kinematics` | hand position, eye position trajectories |
| `block_summary` | block 평균 accuracy, mean RT |
| `session_meta` | day, dist, expType, isexercise |
| `subject_meta` | subID, age, sex (코드에 있으면 — 보통 별도 csv) |
| `rng_state` | par.scheduleRngState, expData.seedRand |
| `other` | 위에 안 맞는 모든 것 |

| `format` | 의미 |
|---|---|
| `int`, `float`, `string`, `bool`, `array`, `matrix`, `struct`, `csv-row`, `json`, `image`, `binary`, `other` |

**struct 저장 시**: `save('finalState.mat', '-struct')` 한 번에 여러 채널이 들어가도 — 한 entry of `format=struct` PLUS 주요 sub-field 들을 별도 entry 로 분리. PostgreSQL consumer 가 채널별 query 가능하게.

## `display` — 시각 출력

```json
"display": {
  "stimulus_outputs": [
    {
      "kind": "draw",
      "name": "Screen('DrawDots') — random-dot motion",
      "drives": ["coherence", "direction", "speed"],
      "evidence": ["display_dots.m:34"]
    },
    {"kind": "flip", "name": "Screen('Flip')", "evidence": ["main_duration.m:75"]}
  ],
  "figure_outputs": [
    {
      "sink": "figs/<subID>_psychometric.png",
      "what": "Psychometric curve per condition",
      "evidence": ["plot_results.m:22"]
    }
  ]
}
```

`stimulus_outputs[].kind ∈ {draw, flip, fixation, feedback, stimulus, instruction, other}`. `drives[]` 는 어떤 factor/parameter 가 그 자극의 모양을 결정하는지.

## `storage` — 저장 경로

```json
"storage": {
  "data_paths": [
    {"path": "/Volumes/CSNL_new-1/people/JOP/Magnitude/Data/Time2Dist/<subID>", "kind": "per_session_log", "format_hint": "MATLAB .mat"},
    {"path": "./data/<expName>_<date>", "kind": "per_session_log", "format_hint": "PsychoJS csv"}
  ],
  "backup_paths": ["/Volumes/CSNL_backup/Time2Dist/"],
  "naming_convention": "<subID>_<day>_<phase>.mat 또는 <pid>_<expName>_<YYYY-MM-DD>.csv"
}
```

경로는 **verbatim** 으로 기록. resolve 안 함 (`/Volumes/...` 가 그대로면 그 자체가 재현성 정보).

## `reproducibility` — 재현성 점수

```json
"reproducibility": {
  "seed": {
    "pinned": true,
    "source": "saved RNG state in trial_schedule.mat (par.scheduleRngState)",
    "scope": "per_subject",
    "evidence": "make_trial_schedule_duration.m:35"
  },
  "randomization": {
    "scheme": "fixed_schedule",
    "description": "Pre-generated schedule from make_trial_schedule_duration.m, replayed deterministically per session"
  },
  "version_pinning": { "total": 8, "pinned": 6, "lockfile_present": false },
  "environment_capture": {
    "files_found": ["requirements.m", "setup_environment.m"],
    "completeness": "partial"
  },
  "score": {
    "overall": 92,
    "components": {
      "seed": 25, "randomization": 15, "version_pinning": 12, "env_capture": 20, "deterministic_paths": 15
    },
    "notes": "SCHEDULE_ACTIVE 패턴 — gold standard reproducibility (seed + randomization 자동 만점)"
  }
}
```

점수 채점 자세히: [reproducibility-and-rigor.md](./reproducibility-and-rigor.md).

## `rigor` — 엄밀성 점수

```json
"rigor": {
  "counterbalancing": { "present": true, "scheme": "subjNum mod 4 → AB-BA / AB-AB / BA-AB / BA-BA", "evidence": "make_trial_schedule_duration.m:35-50" },
  "sample_size_justification": { "present": true, "method": "ad_hoc", "evidence": "docs/protocol.md:8 'N=20 명, 선행 연구 (Acerbi 2014) 기준'" },
  "blinding": { "applicable": false, "experimenter_blind": null, "participant_blind": null, "note": "Single-subject within-subject design — blinding 불필요" },
  "preregistration_marker": { "present": false, "url_or_id": null },
  "exclusion_rules": { "rules_found": ["RT < 200 ms 제외 (analyze.m:34)", "accuracy < 0.5 인 블록 제외 (analyze.m:42)"] },
  "checks": {
    "every_factor_has_role": true,
    "no_single_value_factor": true,
    "saved_5_categories_present": true,
    "hierarchy_complete": true,
    "no_dead_branches_in_conditions": true,
    "schedule_consistency": true
  },
  "score": { "overall": 78, "notes": "..." }
}
```

## `adaptive_procedure` — 적응형 절차 (있을 때만)

```json
"adaptive_procedure": {
  "family": "staircase",
  "engine": "upDownStaircase(1, 2, initialThresh=10, stepsize=3, 'levitt')",
  "update_rule": "1-up-2-down Levitt halving on reversal indices 1,3,7,15,... — target 70.7%",
  "rule_confidence": "high",
  "n_interleaved": 3,
  "interleaving_key": "task.parameter.orientation",
  "termination": "n_trials = 100 per staircase (outer budget, no auto-stop)",
  "per_trial_state_saved": ["s.response[]", "s.strength[]", "s.reversals[]", "s.threshold", "s.stepsize"],
  "warm_start": { "enabled": false, "mechanism": null },
  "evidence": ["taskTemplateStaircase.m:181", "upDownStaircase.m:61-66"]
}
```

적응형 절차가 없으면 `null`.

`family ∈ {staircase, quest, quest_plus, psi_kontsevich_tyler, bayesian_adaptive, pest, custom, unknown}`.

`rule_confidence`: `high` (literal 직독) / `medium` (helper 시그니처 추론) / `low` (외부 config 에서 로드 — open_question 추가됨).

`per_trial_state_saved = []` (빈 배열) 이면 **only final estimate saved** → randomization 점수가 partial 로 떨어집니다.

## `open_questions[]` — 미해결 질문

```json
"open_questions": [
  {
    "topic": "parameters",
    "question": "par.feedback_duration_ms 가 README 에는 있는데 코드에 안 보입니다. 어디서 설정되나요?",
    "evidence": "docs/protocol.md:24 mentions 'feedback 200ms' but no code site found",
    "options": ["main_duration.m 의 어딘가", "별도 config 파일", "잘못된 README", "건너뜀 / 모름"]
  }
]
```

`topic ∈ {identity, platform, hierarchy, factors, conditions, parameters, saved_variables, display, storage, reproducibility, rigor}`.

인터뷰 (Pass 12) 가 풀면 빠지고, 못 풀면 출력에 남아 PostgreSQL consumer 가 queue 로 띄울 수 있습니다.

## `provenance`

```json
"provenance": {
  "plugin_version": "0.2.0",
  "schema_version": "1.1.0",
  "analyzed_at": "2026-05-22T18:42:11Z",
  "model": "claude-opus-4-7",
  "passes_run": ["survey", "platform", "hierarchy", "factors", "conditions", "parameters", "saved", "display", "storage", "reproducibility", "rigor", "interview-1", "interview-2"],
  "source_root": "/Volumes/CSNL_new-1/people/JOP/Magnitude/Experiment/Time2Dist",
  "bytes_analyzed": 287_412,
  "files_analyzed": 47,
  "researcher_initial": "JOP"
}
```

- `analyzed_at` 은 ISO 8601 UTC.
- `passes_run` 은 실제로 실행된 pass 순서대로. 인터뷰가 여러 round 면 `interview-1`, `interview-2`, …
- `researcher_initial` 은 슬래시 커맨드 인자 `RESEARCHER_INIT=` 값.

---

## "Evidence-or-silence" 원칙

**모든 `evidence` 배열은 최소 1개 entry 가 있어야 합니다** (단, interview 답변으로 채운 경우 `interview: <q-hash>` 로 대체).

```json
{ "evidence": ["main_duration.m:34", "make_trial_schedule_duration.m:18-22"] }
{ "evidence": ["interview: q-d4a7"] }
```

근거가 없으면 그 필드는 `null` + `open_questions[]` 에 들어갑니다. **절대로 추측한 값을 채우지 않습니다**. 이게 anatomist 의 Hard rule 2 — *No invention*.
