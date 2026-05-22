# 플랫폼별 가이드

각 프레임워크가 어떻게 인식되는지, 어떤 부분을 잘 잡고, 어디에서 함정에 빠지기 쉬운지 정리합니다. 자세한 detection rule 은 [`prompts/lenses/*.md`](../prompts/lenses/) 의 lens 파일들이 ground truth.

## Psychtoolbox (MATLAB)

**감지 시그널**: `Screen('OpenWindow'`, `Screen('Flip'`, `KbCheck`, `KbWait`, `PsychDefaultSetup`, `WaitSecs`.

**잘 잡는 것**

- 트리 루프 구조: `for iR = 1:nBlocks` / `for iT = 1:nT`. 변형 (while, recursion) 도 인식.
- CSNL 표준 컨벤션:
  - `par.X{iR}(iT)` 형식의 per-trial 저장
  - `par.tp.<channel>{iR}(iT)` per-trial timing (cell-of-cell — 각 채널을 별 entry 로 split!)
  - `par.results.X(iR)` per-block summary
  - `par.subID|day|dist|expType|isexercise` per-session meta
- Pre-generated schedule 패턴:
  - `make_<exp>_schedule.m` 생성기 + `load(*schedule*.mat)` + `par.scheduleRngState`
  - 활성 시 `factor.level_source="inline-literal"`, `randomization.scheme="fixed_schedule"`, FULL seed credit (gold standard)
- Kinematic IVs (motion experiments): `par.kin.speed1`, `par.stim.dir1`, `par.trial.tvm1` 등 generator 파일이 entry 와 떨어져 있어도 `StimGenerator*.m` / `*Trajectory*.m` / `*Kinematic*.m` 파일명을 함께 끌어옴.

**함정**

- `par.tp` 구조체를 **하나의 entry 로 collapse 하면 안 됨** — `vbl_start`, `vbl_cue`, …, `vbl_resp`, `tend` 채널이 각각 별 entry. 자동으로 split 합니다.
- `subID`, `day`, `dist` 가 `finalState` 구조체 안에 들어있어도 — 그 안의 sub-field 들을 별 saved_variable entry 로 분리해야 PostgreSQL 에서 채널별로 query 가능.
- 헤더 코멘트 `% Timing: tprecue 0.5->0.3` 은 **change log**, 현재 값이 아님. body assignment 우선.
- `mod(subjNum, N)` 분기는 between-subject CB. `par.day == N` 분기는 within-subject phase 분리. 둘 다 정확히 잡아야 함.
- Pre-gen schedule 활성 시 — `n_blocks`, `n_trials_per_block` 을 **literal 에서 우선** 읽고, schedule `.mat` cell-array 차원은 **sanity check**. 불일치 시 `rigor.checks.schedule_consistency = false` + open_question.

**적응형 절차** (자세히: [reproducibility-and-rigor.md § adaptive](./reproducibility-and-rigor.md#adaptive))

- `upDownStaircase(nup, ndown, init, step, rule)` — Levitt vs PEST 절대 섞지 않음.
- `QuestCreate` / `QuestUpdate` / `QuestQuantile` (Quest 1).
- `qpInitialize` / `qpQuery` / `qpUpdate` (QUEST+, Watson 2017).
- `psybayes(psy, method, vars, xi, yi)` (Acerbi PSI).

---

## mgl (Justin Gardner) — MATLAB

**감지 시그널**: `mglOpen(`, `mglFlush;`, `mglBltTexture`, `mglGetKeyEvent`, `initTask(`, `updateTask(`, `tickScreen(`.

PTB 와 **mutually exclusive** — 둘이 동시에 fire 하면 `ptb-mixed` 로 demote.

**세 가지 sub-mode** (`platform.variant`)

| Variant | 특징 | 누가 쓰나 |
|---|---|---|
| `mgl-callback` | `initTask` + `@startSegmentCallback` 등 callback 등록 + `while ... updateTask ... tickScreen ... end` 루프. trial 카운트는 `task.numTrials × task.numBlocks` 또는 `task.parameter.X` cardinality. | Gardner Lab `grustim` 의 거의 모든 실험 (alaisburr, cohcon, afcom 등) |
| `mgl-primitive` | mgl primitive 들 (`mglOpen`, `mglFlush`, `mglCreateTexture`, `mglGetKeys`) 만 쓰고 callback framework 가 **call graph 어디에도 없음**. 명시적 `for iT = 1:nT`. | (드묾) |
| `mgl-hybrid` | entry 파일은 primitive 모드 (callback 없음) 인데 같은 디렉토리에 framework 파일 (`taskTemplate.m`, `initTask.m`, ...) 이 library include 로 공존. | **HJL Main_RingExp** 의 canonical case |

**잘 잡는 것**

- `task.parameter.X = [...]` → 크로스된 within-trial factor (level_source=inline-literal).
- `task.randVars.uniform.X` → uniformly-sampled per-trial factor.
- `task.randVars.calculated.X` → **response slot, factor 아님** — saved_variables 로만 emit. 흔한 LLM 실수 자동 방지.
- `task.segmin`/`segmax`/`segquant` 로 segment timing 모델.
- `task.synchToVol = [0 1]` → fMRI volume-locked segment.
- Eye-tracker variants: `mglEyelinkSetup(` → EyeLink, `writeDigPort(` + `eyeCalibrationASL` → ASL, `eyeCalib9.m` → 9-pt manual.
- Cross-run warm-start: `getLastStimfile(myscreen)` + `stimulus.<X>Staircase{end+1}` → 재현성 노트에 "warm-start adaptive from prior stimfile" 추가.

**함정**

- **mgl 의 trial 루프는 `for iT = ...` 가 아닙니다** (callback mode). `task.numTrials` 가 `inf` 가 default — budget 은 `task.numBlocks × prod(numel(task.parameter.X))` 에서 emerge.
- **`task.thistrial.X` 는 factor 가 아닙니다.** 현재 trial 의 값일 뿐. level 은 `task.parameter.X = [...]` 에서 (assignment) 또는 `expBlock.<X>Seq` 생성기에서.
- **`task.private`** 는 mgl-valid 슬롯 — MATLAB OOP `private` 키워드와 무관.
- **Dated `<name>_YYMMDD.m` 파일들은 evolution chain**. HJL 의 `psychExpPdmCds_110622` → ... → `psychExpPdmCds_120520` 은 한 프로젝트의 monthly snapshot. 25개를 separate experiment 로 세지 마세요. canonical entry picker 가 자동으로 latest-dated 만 골라줍니다 (`*~`, `*.svn-base`, `conflicted copy`, `*orig.m` 자동 제외).
- **SVN `*.svn-base` 800+ 개**: SVN 작업 사본 그림자 — separate script 아님. 파일 카운트에서 제외.
- **mgl + ASL/EyeLink/9-pt 함께 있어도 entry 가 `eyeCalibDisp` 를 call 안 하면 "no eye tracking"** (HJL psychophysics scripts). 디렉토리 file presence 만으로 판단 X.

---

## PsychoPy — Python (Coder)

**감지 시그널**: `from psychopy import ...`, `visual.Window`, `win.flip()`, `<stim>.draw()`, `event.waitKeys`, `data.TrialHandler`.

**잘 잡는 것**

- `data.TrialHandler(trialList=..., nReps=N)` — trial count = `N × len(trialList)`. `MultiStairHandler`, `TrialHandlerExt`, `StairHandler` 모두 인식.
- `thisExp.addData('name', value)` 의 모든 call site → 한 column 씩 saved_variables.
- `data.importConditions('cond.csv')` → factor 의 `level_source: conditions-file`. CSV 컬럼명 = factor name.
- Seed: `numpy.random.seed(s)`, `random.seed(s)`. `s` 가 `expInfo['participant']` 면 deterministic per-subject.

**함정**

- conditions.csv 컬럼이 factor 인데 — 코드에는 `thisTrial['contrast']` 만 보임. 레벨 list 는 csv 안에 있어서 코드만 봐선 enumerate 불가 → open_question 자동.
- `expInfo['session']` 가 metadata string 인지 within_subject 축인지 — code 가 그것 위에서 branch 하면 factor, 아니면 subject_meta.
- Builder export 의 `.py` 는 auto-generated noise (`thisComponent.tStart = ...`) 가 많음 — 그것이 IV/parameter 가 아님을 lens 가 인식.

---

## PsychoJS Builder export — JavaScript

**감지 시그널 — 4-파일 fingerprint 가 필수지만 not sufficient.**

같은 디렉토리에 모두 있어야:

- `<name>.psyexp` (XML 원본)
- `<name>.js` (자동 생성 ES module runtime, 보통 4 000–8 000 lines)
- `<name>-legacy-browsers.js` (IIFE fallback)
- `index.html` (title 끝에 `[PsychoPy]` 박힘)

**추가로 Scheduler-graph 시그널 ≥3 필수** — 4-파일만 있으면 `psychojs-handwritten`. 진짜 Builder 는 다음을 함께 emit:

- `const flowScheduler = new Scheduler(psychoJS);` + 연속된 `flowScheduler.add(...)` cascade
- `<routine>RoutineBegin(snapshot)` 보일러플레이트
- `if (currentLoop === psychoJS.experiment) { psychoJS.experiment.nextEntry(snapshot); }`
- `psychoJS.experiment.addData('<routine>.started', globalClock.getTime())` + 매칭되는 `.stopped`

**잘 잡는 것**

- xlsx 컬럼 → factor 매핑:
  - `nunique == 1` → parameter (constant scalar), 아니라 factor
  - `nunique ≤ 8` discrete → categorical factor
  - `nunique ≥ 10` numeric 등간 → continuous factor (design variable)
  - `nunique == row_count` string-like → stimulus catalog (factor 아님)
  - 50%+ None → metadata
  - 두 컬럼이 row-by-row bijection → 하나로 collapse (예: `ecc_idx` ↔ `ecc_deg`)
- Routine triple grouping: `<r>RoutineBegin / EachFrame / End` 를 ONE routine 노드로 묶음 (3개 sibling function 으로 흩어놓지 않음).
- Auto-component telemetry (`<routine>.started`, `<routine>.stopped`, `<slider>.response`, `<slider>.rt`, `<kb>.keys`, `<mouse>.x/y/leftButton/...`) vs researcher-added `addData(...)` columns 분리.
- Prolific/Pavlovia: `psychoJS.setRedirectUrls(...)`, `util.addInfoFromUrl(expInfo)`.

**함정**

- **"config-as-conditions" 트릭**: 1-row xlsx 의 모든 컬럼이 nunique==1 이면 — 그건 6-factor × 1-level 디자인이 아니라 **parameter sidecar**. MSY 의 `session_loop.xlsx` 가 정확히 이 패턴 (6 columns × 1 row of integer scalars).
- `nReps: nrep_block_test` 처럼 **identifier** 일 때 — 값을 `importConditions(snapshot)` 체인으로 추적해서 모-loop 의 xlsx 컬럼까지 돌아가야 함.
- `trialList: undefined` 가 Builder TrialHandler 안에 있으면 schedule 이 **다른 곳에 있다** 는 fingerprint — `TrialHandler.importConditions(...)` outside any `new TrialHandler({...})` 를 grep 해서 hand-written shuffle 찾기 (BYL biasVar 패턴).
- Builder 의 auto-noise 를 critique 하지 않기 — `typeof 'space' === 'string' ? ['space'] : 'space'` 같은 tautological 가드는 Builder template fingerprint, bug 아님.
- `_e_1` / `_m_1` 같은 suffix 는 Builder 의 component-naming (Routine 복제 시 자동 부여) — researcher 의 confusion 아닌 parallel stream (exercise vs main).

---

## jsPsych — JavaScript

**감지 시그널**: `import { initJsPsych }`, `jsPsych.init(`, `jsPsych.data.addProperties(...)`, `randomization.factorial(...)`, `timeline_variables: [...]`.

**잘 잡는 것**

- `factorial_design` → factor 들이 명시적으로 enumerate.
- `timeline_variables` → conditions 의 grid.
- `jsPsych.data.write(...)` 의 모든 sink.

**함정**

- jsPsych v6 vs v7 API 차이 — `initJsPsych()` 객체 vs class. lens 가 둘 다 인식.
- `jsPsych.data.addProperties({...})` 는 saved_variable 인데 — `block_summary` 인지 `subject_meta` 인지는 scope 에 따라 다름.

---

## lab.js — JavaScript

**감지 시그널**: `new lab.flow.Sequence({content:[...]})`, `lab.html.Screen`, `lab.canvas.Sequence`.

generic 렌즈가 적용되지만 lab.js-specific 한 단서 (`Form` 컴포넌트의 `responses` 키, content array nesting) 는 인식.

---

## external — 외부 호스팅

**감지 시그널 — 양방향 모두 필요**:

- **Negative**: ≥3 데이터 파일 (`.csv` / `.psydat` / `.mat`), NO `Screen(` / `visual.Window` / `mglOpen` / `initJsPsych` 호출이 로컬 어디에도 없음.
- **Positive (필수)**: 문서에 명시된 URL — Pavlovia (`pavlovia.org/run/<id>` 또는 `<user>.pavlovia.org/<exp>`), Gorilla study URL, jsPsych-shop deployment, GitHub repo URL, paper-companion URL 중 하나.

**둘 다 만족할 때만 `framework="external"`.** Positive evidence 가 없으면 (작은 pilot tree 등) `framework="unknown"` + open_question 으로 갑니다 — false-positive 방지.

**external 일 때 채우기**

```json
"platform": {
  "framework": "external",
  "external_host": {
    "kind": "pavlovia",
    "url": "https://pavlovia.org/run/MSY/cat_mag_main_ses1",
    "evidence": "README.md:12 cites 'task hosted on pavlovia.org/MSY/cat_mag_main_ses1'"
  }
}
```

`hierarchy`, `factors[]`, `conditions[]` 는 저장된 데이터 컬럼 + paper Methods 에서 추론 가능한 만큼만. 못 정한 모든 것은 `open_questions[]`.

**자주 보는 케이스**

- HSL_MSY 워크스페이스 — 데이터만 로컬, code 는 다른 사람 GitHub.
- Acerbi/Stocker 의 paper-companion repo — data + model 코드만, 자극 제시 코드는 미공개. `external_host.kind = "github-elsewhere"` 또는 lab-private 으로.

---

## custom / mixed / unknown

위 어느 것에도 안 맞으면 [`prompts/lenses/generic.md`](../prompts/lenses/generic.md) 적용.

- `for i in 1:nT` / `for (let i=0; i<n; i++)` / `for (i in 1:N)` 의 innermost loop 가 trial unit.
- SCREAMING_SNAKE constant (`N_TRIALS`, `ITI_MS`, `FEEDBACK_MS`) → parameters[] 자동 추출.
- `rows.append({...})` + `pd.DataFrame.to_csv(...)` (Python) / `rbind(results, ...)` + `write.csv(...)` (R) / `results.push({...})` (JS) → saved_variables.
- Seed: `random.seed`, `np.random.seed`, `set.seed`, `seedrandom`, `chance.js`.

**한계**: paradigm-specific inductive bias 가 없으므로 정확도가 framework-specific lens 의 70% 정도. 가능하면 코드를 PsychoPy/PTB/mgl 같은 표준 프레임워크로 옮기는 게 좋습니다.

---

## 한 디렉토리에 여러 플랫폼이 섞여 있을 때

흔한 경우: `.psyexp + .py + .js` (Builder dual export) 또는 `.m + .py` (분석 일부가 Python).

- 분석 코드는 [`db/csnl-conventions.json`](../db/csnl-conventions.json) 의 `analysis_exclusion_signatures` (e.g. `analyze_*`, `proc_*`, `plot_*`, `fig_*`, `extract_*`, `qc_*` filename + `.nii`, `NIfTI`, `SPM`, `FSL`, `AFNI`, `fMRIPrep`, `BIDS`, `mrtools`, EyeLink `.edf` parsing 등) 가 자동 제외.
- Dual-export 는 `platform.framework = "psychojs-builder"` + `platform.runtimes = ["python-desktop", "javascript-web"]` 로 한 entry.
- `mixed` 는 framework 들이 진짜로 섞여 한 paradigm 을 구성할 때만 (rare).

---

## 함정 정리

| 함정 | 어디서 |
|---|---|
| Header 코멘트 change log 를 현재 값으로 오해 | PTB |
| `par.tp` cell-of-cell 을 단일 entry 로 collapse | PTB (CSNL) |
| `task.thistrial.X` 를 factor 로 오해 | mgl |
| `task.randVars.calculated.X` 를 factor 로 emit (실제론 response slot) | mgl |
| Dated `<name>_YYMMDD.m` 들을 separate experiment 로 카운트 | mgl (HJL) |
| `*.svn-base` 800+ 개를 file count 에 포함 | mgl (HJL) |
| 4-파일 fingerprint 만 보고 Builder 로 promote (Scheduler graph 미확인) | PsychoJS |
| Auto-component telemetry 를 researcher-added column 과 섞어서 response count 인플레이션 | PsychoJS Builder |
| `nReps: <identifier>` 의 값을 0 또는 1 로 추측 | PsychoJS Builder |
| 1-row config xlsx 를 6-factor × 1-level 디자인으로 오해 | PsychoJS Builder |
| Pre-gen schedule 활성 시 RNG-sampled 로 분류 | PTB (CSNL pre-gen) |
| Within-subject CB 를 between-subject 로 분류 | PTB (generator 못 읽으면) |
| Levitt 와 PEST staircase 를 동일 시 | 모든 adaptive |
| Quest 와 Bayesian adaptive 를 동일 시 (Quest 는 Weibull + single threshold) | 모든 adaptive |
| `method='random'` TrialHandler + adaptive-naming 변수를 adaptive 로 오해 | PsychoPy / PsychoJS |
| 작은 pilot tree (data 만, 무 코드) 를 external 로 false-promote | 모든 |
| 분석 코드 (`analyze_*`, `.nii` 참조) 를 실험-진행 코드로 오해 | 모든 |

이런 함정들이 모두 v0.2 lens 에 explicit guard 로 들어가 있습니다. 새로운 함정을 발견하면 PR 환영.
