# experiment-anatomy

> **실험 코드를 펼쳐놓으면 Opus 가 한 시간 안에 다 읽고 표준 형식으로 정리해줍니다.**
> Psychtoolbox · mgl · PsychoPy · PsychoJS Builder · jsPsych · lab.js — 무엇으로 짰든 같은 모양의 JSON 한 장이 나옵니다.

```
$ /experiment-anatomy:analyze /Volumes/CSNL_new-1/people/JOP/Magnitude/Experiment/Time2Dist
✦ Pass 1 — 트리 훑기 (47개 파일, 280KB 읽음)
✦ Pass 2 — 플랫폼: psychtoolbox (변형 없음), confidence 0.97
✦ Pass 3 — 계층: session: par.day 1..5 (within_subject); block: for iR=1:nBlocks; trial: for iT=1:nT
✦ Pass 4 — pre-generated schedule 패턴 감지됨 → 생성기 make_trial_schedule_duration.m 우선 읽음
✦ Pass 5 — 조작변수 3개: dist (within_subject), day (within_subject), tprecue (per_trial)
✦ Pass 6-9 — 파라미터 41개, 저장변수 28개, 디스플레이 5개, 저장경로 2개
✦ Pass 10 — 재현성 92/100 (SCHEDULE_ACTIVE 자동 만점)
✦ Pass 11 — 엄밀성 78/100
✦ Pass 12 — 확인 인터뷰 (질문 2개)
   Q1: dist 변수 레벨이 [short, long] 이 맞나요? (make_trial_schedule_duration.m:18)
   Q2: par.exclude.rt_min = 0.2 가 분석 단계 제외 기준인가요? (analyze.m:34)

→ experiment-spec.json (1.7 KB, schema 1.1.0 통과)
→ experiment-spec-summary.md (한국어 요약 80줄)
```

---

## 이 플러그인이 도와주는 5가지 상황

**1) 논문 메소드 섹션 정리할 때**
세션 수, 블록 수, 조작변수와 레벨, counterbalancing 방식, 제외 기준 — 코드에서 직접 뽑아 정리해 둡니다. 메소드 글을 쓸 때 "어… 그 변수 어디에 있더라" 하며 다시 코드 뒤지는 시간을 줄여줍니다.

**2) 후배에게 코드 인계할 때**
새로 들어온 사람이 코드를 읽기 전에 이 JSON + 요약 마크다운을 먼저 보면, 어떤 변수가 어디에 저장되는지, 어떤 파일이 schedule을 만드는지, 어떤 .mat 이 핵심인지 한눈에 잡힙니다.

**3) 랩 DB 에 새 실험을 등록할 때**
모든 연구자의 모든 실험이 같은 JSON 모양으로 나옵니다. PostgreSQL `experiment_specs` 테이블에 그대로 적재되어 — "조작변수에 contrast 가 들어간 실험 모두 찾아줘" 같은 lab-wide 검색이 가능해집니다.

**4) 재현성·엄밀성 자체 점검할 때**
seed 가 pinned 되었는지, schedule 이 저장되는지, 제외 기준이 코드에 있는지 — 0–100점 채점이 됩니다. 점수보다 **각 component 가 왜 그 점수인지 코드 라인 근거**가 함께 나옵니다. 논문 리뷰어가 묻기 전에 스스로 확인할 수 있습니다.

**5) 다른 사람의 코드를 빠르게 파악할 때**
GitHub 에서 본 paradigm 을 따라 해 보고 싶을 때, README 만 봐서는 모를 구조 (몇 세션? 몇 블록? counterbalance 어떻게? saved variable 어디에?) 가 30분 안에 정리됩니다.

---

## 어떤 코드를 받아주나

| 플랫폼 | 언어 | 인식하는 변형 |
|---|---|---|
| **Psychtoolbox** | MATLAB | CSNL pre-generated schedule (`make_*schedule*.m` + `trial_schedule.mat` + `par.scheduleRngState`) · 실시간 `randperm`/`Shuffle` · staircase / Quest / Quest+ / PSI / Bayesian adaptive |
| **mgl** | MATLAB | `mgl-callback` (Gardner Lab 표준) · `mgl-primitive` (HJL Main_RingExp 스타일, `for iT=1:nT` 명시) · `mgl-hybrid` (entry 는 primitive 인데 같은 폴더에 framework 파일이 공존) |
| **PsychoPy** | Python | Coder (`from psychopy import …`) · Builder export 의 desktop `.py` runtime |
| **PsychoJS Builder** | JavaScript | `.psyexp` + `<name>.js` + `index.html` + `<name>-legacy-browsers.js` 네 파일 묶음. Scheduler graph 검사로 hand-written PsychoJS 와 구분 |
| **jsPsych** | JavaScript | `initJsPsych` + `timeline` + `randomization.factorial` |
| **lab.js** | JavaScript | `new lab.flow.Sequence({content:[…]})` 트리 |
| **외부 호스팅 (`external`)** | n/a | Pavlovia / Gorilla / OSF / paper-companion GitHub 에 코드가 있고 로컬에는 데이터만 있을 때 |
| **그 외** | — | `custom` / `mixed` 로 분류하고 generic 렌즈 적용 |

각 플랫폼마다 **"이 곳을 봐야 한다"는 inductive bias** 가 코딩되어 있습니다 — PsychoJS Builder 의 xlsx 결합 방식, mgl 의 `task.parameter` vs `randVars.calculated` 구분 (앞은 factor, 뒤는 response slot), CSNL `par.tp` cell-of-cell timing 채널 같은 디테일까지.

---

## 30초 만에 시작하기

```bash
# 1. 마켓플레이스 등록 + 설치 (한 번만)
/plugin marketplace add CSNL-vnilab/experiment-anatomy
/plugin install experiment-anatomy@experiment-anatomy-marketplace

# 2. 분석 — 실험 폴더 경로를 인자로
/experiment-anatomy:analyze /path/to/your/experiment SHORT_ID=MyExp PARADIGM_GENRE=estimation RESEARCHER_INIT=ABC

# 3. 두 파일이 현재 디렉토리에 생성됨
ls
# experiment-spec.json           ← 표준 JSON (DB 적재용)
# experiment-spec-summary.md     ← 한국어 80줄 요약 (사람용)
```

자세한 설정·troubleshooting 은 [INSTALL.md](./INSTALL.md) 참고.

---

## 무엇을 정리해주나 — 11개의 절

JSON 한 장 안에 다음이 모두 들어갑니다. 각 절은 **증거 (`evidence`)** 배열로 코드 파일·라인 또는 인터뷰 응답을 함께 기록합니다.

| 섹션 | 무엇 |
|---|---|
| `identity` | 실험 이름, 짧은 ID, paradigm 장르 (psychophysics / estimation / decision / …), 2–4문장 요약 |
| `platform` | framework (mgl / psychojs-builder / external …), variant (mgl-hybrid 등), language, runtimes[] (Builder 의 .py + .js 양쪽), 외부 호스팅이면 `external_host { kind, url }` |
| `hierarchy` | session → phase → block → trial 의 모든 카운트 + `one_liner` 한 줄 ("session: par.day 1..5; block: nBlocks; trial: nT") |
| `factors[]` | 조작변수마다 `name`, `levels`, `type` (categorical/continuous/ordinal), `role` (between/within_subject/within_session/per_trial/derived), `level_source` (inline-literal / conditions-file / rng-sampled / adaptive) |
| `conditions[]` | 실제로 실행된 factor 조합. Cartesian explosion 안 합니다 (Latin-square 같은 CB 스킴은 `design_matrix_summary` 자유 텍스트로) |
| `parameters[]` | 타이밍, 화면 기하, 자극 셋업 같은 setup 상수. `shape ∈ {constant, vector, expression, input}` |
| `saved_variables[]` | 출력 데이터. 5 scale (per_trial/block/session/subject/global) × 9 category (stimulus/response/timing/kinematics/block_summary/session_meta/subject_meta/rng_state/other) 격자 위에 배치 |
| `display` | `stimulus_outputs[]` (참가자가 보는 것) + `figure_outputs[]` (실험자가 저장하는 그림 — saveas/savefig/plt.savefig 등) |
| `storage` | `data_paths[]` verbatim (resolve 안 함 — `/Volumes/...` 가 그대로면 그 자체가 재현성 정보) + `naming_convention` |
| `reproducibility` | seed pinning, randomization scheme, version pinning, environment capture, deterministic paths — 각각 component 점수와 함께 총 0–100점. SCHEDULE_ACTIVE / ADAPTIVE_REPLAYABLE 패턴은 자동 만점 |
| `rigor` | counterbalancing, sample-size justification, blinding, preregistration, exclusion rules, static checks — 총 0–100점 |
| `adaptive_procedure` | staircase / Quest / Quest+ / PSI / Bayesian adaptive 가 있을 때만. family + 정확한 update_rule + per-trial state 저장 여부 + termination |
| `open_questions[]` | 코드만으로 못 정한 모든 것 — 인터뷰에서 풀리면 빠지고, 안 풀리면 출력에 남아 PostgreSQL 컨슈머가 큐로 띄울 수 있음 |
| `provenance` | plugin/schema 버전, 분석 시각, 모델, 읽은 바이트수, 연구자 initial |

각 필드의 자세한 한국어 해설은 [docs/output-fields.md](./docs/output-fields.md) 참고.

---

## 어떻게 정확한가 — 왜 믿을 수 있나

**12-pass 워크플로우.** 한 번에 욕심내지 않고 — 트리 훑기 → 플랫폼 식별 → 계층 → factor → condition → parameter → saved variable → display → storage → reproducibility → rigor → 인터뷰 순서로 진행합니다. 각 pass 가 자기 섹션을 채우고, 뒤 pass 가 앞 섹션의 evidence 를 보강합니다.

**7개 platform-specific 렌즈.** [`prompts/lenses/*.md`](./prompts/lenses) 에 plat마다 "이 곳을 봐야 한다, 이 패턴은 이렇게 해석한다, 이런 함정에 빠지지 마라" 가 코딩되어 있습니다. PsychoJS Builder 의 4 000 라인 자동 생성 .js 가 헷갈리게 보여도 lens 는 보일러플레이트와 연구자 코드를 구분합니다.

**실제 lab 코드 33+ 샘플로 보정.** [`db/csnl-conventions.json`](./db/csnl-conventions.json) — CSNL 10명 연구자 (BYL, BHL, DG, JHR, HSL_MSY, JOP, JSL, KY, MSY, HJL) 의 실험 코드 컨벤션. [`db/external-samples.json`](./db/external-samples.json) — Gardner Lab (Stanford) · Acerbi Lab (Helsinki) · Stocker Lab (UPenn) · Sims Lab (RPI) · Brainard · Wichmann · Wei Ji Ma · Gold · Pelli · Wandell 의 공개 코드 33 샘플. 이 두 DB 의 패턴이 lens 의 inductive bias 가 됩니다.

**Codex 어드버서리얼 리뷰 통과.** v0.2 디자인은 Codex 가 7 CRITICAL + 5 MEDIUM 이슈를 잡았고, ship 전에 모두 해소됐습니다 — schema enum drift, mgl 두-모드 분류 실패, PsychoJS Builder false-positive, missing 스키마 필드, 미해결 adaptive rule 의 hard-rule 충돌, lens loading 명시, adaptive 재현성 auto-credit, external false-positive 등. 자세한 내역은 [`v0.2.0 changelog`](#changelog) 참고.

**"모르는 건 묻는다" 가 default 동작.** Pass 12 가 한국어로 한 번에 한 질문씩, 코드 라인 근거 + 4지선다 + "건너뜀/모름" 옵션을 함께 띄웁니다. 절대로 추측한 값을 채우지 않습니다 (Hard rule 2 — *No invention*).

**증거-or-침묵.** 모든 필드의 `evidence` 배열은 `path/file.ext:line` 또는 `interview: <hash>` 가 들어 있어야 합니다. 근거가 없으면 그 필드는 `null` + `open_questions[]` 에 등록됩니다. 어림짐작으로 "42" 나 "subjNum" 같은 값을 채우지 않습니다.

---

## 인터뷰 모드 — 모르는 건 묻습니다

코드만으로 못 정한 게 있으면 (i) Pass 12 가 ≤10개 한국어 질문을 던지고, (ii) 답변이 들어오면 즉시 spec 에 반영합니다.

```
✦ Pass 12 — 확인 인터뷰

Q1 (factors):
  par.exclude.rt_min = 0.2 (analyze.m:34) — 이 값이…
  ① 분석 단계 제외 기준 (trial level RT cutoff)
  ② 실험 진행 중 제외 기준 (online 제외)
  ③ 둘 다
  ④ 건너뜀 / 모름
> 1
✦ 반영: rigor.exclusion_rules 에 "RT < 200 ms 제외" 추가, evidence: analyze.m:34
```

**언제 멈추는가**: (a) 모든 material question 이 풀렸을 때, (b) "skip / 그만 / later / 나중에" 라고 답하면, (c) 10개 질문 cap. 남은 질문은 출력에 남아 PostgreSQL 컨슈머가 queue 로 띄울 수 있습니다.

연구자가 "그 factor 는 아니야 / IV 아니야" 라고 push back 하면, 즉시 spec 에서 빼고 `evidence: "interview: researcher confirmed not an IV"` 한 줄 기록합니다. **연구자가 verdict, 에이전트는 harness 일 뿐.**

자세한 인터뷰 동작 원리는 [docs/interview-mode.md](./docs/interview-mode.md).

---

## 랩 DB 통합 (선택)

PostgreSQL `experiment_specs` 테이블 + 6개 child table 에 그대로 적재할 수 있습니다.

```bash
# 한 번만 — DDL 적용
psql "$DATABASE_URL" -f <(awk '/^```sql$/,/^```$/' schemas/postgres-mapping.md | sed '1d;$d')

# 매번 — 분석 후 적재
/experiment-anatomy:export ./experiment-spec.json
# 또는: python3 scripts/upsert-to-postgres.py ./experiment-spec.json
```

업서트는 트랜잭션 안에서 (`BEGIN`/`COMMIT`) 진행되고, `short_id` 가 natural key 라 재실행해도 안전합니다 (UPSERT). 자세한 DDL 과 매핑 로직은 [`schemas/postgres-mapping.md`](./schemas/postgres-mapping.md).

자체 검색·집계 예시:

```sql
-- contrast 가 조작변수에 들어간 모든 실험
SELECT identity->>'title', identity->>'short_id'
FROM experiment_specs es
JOIN spec_factors sf USING (short_id)
WHERE sf.name ILIKE '%contrast%';

-- pre-generated schedule 패턴을 쓰는 실험들
SELECT identity->>'title'
FROM experiment_specs
WHERE reproducibility->'randomization'->>'scheme' = 'fixed_schedule';

-- 재현성 점수 80 이상
SELECT identity->>'title', reproducibility->'score'->>'overall'
FROM experiment_specs
WHERE (reproducibility->'score'->>'overall')::int >= 80
ORDER BY 2 DESC;
```

---

## 자주 묻는 질문 (FAQ)

**Q. Opus 가 비싸면 다른 모델로 돌릴 수 있나?**
A. `agents/anatomist.md` 의 `model: opus` 프런트매터를 바꾸면 됩니다. 다만 12-pass 의 깊이가 가치라서 — Sonnet 까지는 보장하지만 그 아래는 ablate 됩니다.

**Q. 코드가 외부 (Pavlovia / Prolific 호스팅) 에 있는데, 로컬엔 데이터만 있다. 어떻게?**
A. `platform.framework = "external"` 로 분류되고 `external_host { kind, url, evidence }` 가 채워집니다. 데이터 컬럼과 paper Methods 에서 추론 가능한 만큼 spec 을 채우고, 나머지는 `open_questions[]` 에 들어갑니다. 자세한 처리는 [docs/by-framework.md](./docs/by-framework.md) § external.

**Q. 같은 실험을 PsychoPy Builder 로 만들면 .py 와 .js 가 모두 나온다. 어느 쪽이 source of truth?**
A. `.psyexp` (XML 원본) 을 구조의 ground truth 로, `.js` 를 runtime 사이드이펙트 / 데이터 캡처의 ground truth 로 봅니다. `platform.runtimes = ["python-desktop", "javascript-web"]` 으로 양쪽 모두 기록합니다.

**Q. 내 실험은 staircase 라 매 시행마다 stim 이 바뀐다. factor 가 0개라고 나오나?**
A. 아닙니다. `role=per_trial`, `level_source=adaptive`, `levels=[]` 로 한 개의 factor 가 만들어지고, 별도의 `adaptive_procedure` 블록 (family, update_rule verbatim, per-trial state 저장 여부, termination) 이 채워집니다. Levitt vs PEST vs Garcia-Perez 를 절대 섞어 쓰지 않습니다.

**Q. 후배가 .m 파일 200개 짜리 repo 를 줬다. Opus 가 다 읽나?**
A. 디폴트 cap 이 400 KB 입니다. 가장 entry 답고 (`main_*`, `run_*`, `experiment*.py`, `index.html`) 가장 최근에 수정된 파일부터 1-hop callee 까지 우선 읽습니다. 더 많이 읽혀야 하면 `MAX_BYTES=1500000` 같이 키워서 호출 가능.

**Q. 라이센스가 모호한 외부 코드도 받나?**
A. 받지만, 분석 결과 JSON 안에는 라이센스 정보를 따로 기록하지 않습니다 (단, `external_samples.json` 의 외부 lab 카탈로그에는 license 컬럼이 있습니다). 분석 그 자체는 read-only.

**Q. 결과 JSON 을 사람이 직접 손으로 고쳐도 되나?**
A. 됩니다. 다만 schema 검증 (`schemas/experiment-spec.schema.json` 통과) 을 통과해야 PostgreSQL 적재가 안전합니다. `/experiment-anatomy:review` 가 수동 편집 → 재검증 사이클을 도와줍니다.

**Q. CSNL 외 다른 랩에서 써도 되나?**
A. 네, fork 권장. CSNL convention (`par.tp.<channel>` timing, `make_*schedule*.m` 생성기, `participants.csv` 으로 between-subject CB) 가 lens 에 일부 코딩되어 있어서 — 다른 랩의 패턴과 안 맞으면 `prompts/lenses/*.md` 를 prune/replace 하시면 됩니다. PR 환영.

---

## 한계 / 알려진 미지원

- **OpenSesame 1.x / 2.x, E-Prime, Neurobs Presentation, PsyToolkit, Inquisit** — enum 에 자리는 잡혀 있지만 (`opensesame`, `neurobs-presentation`) 전용 렌즈가 없어 generic 처리. 정확도 낮음.
- **R 기반 실험 코드** — generic 렌즈 적용. `library(rstimulus)` 같은 R 전용 패키지를 자동 인식하지 않습니다.
- **Unity / Unreal / 게임 엔진 기반 실험** — 미지원. `custom` 으로 떨어집니다.
- **fMRI / EEG / MEG 분석 코드** — 미지원 (자극 제시 + 응답 캡처 + trial loop 가 있어야 "실험 진행 코드"로 인식). [`db/csnl-conventions.json`](./db/csnl-conventions.json) 의 `analysis_exclusion_signatures` 가 분석 코드를 자동으로 제외합니다.
- **40 MB 넘는 .psyexp / 8 000 라인 넘는 .js** — 한 번에 못 읽음. 핵심 영역 (Routines, Loops, addData 사이트) 만 우선 샘플링하고 나머지는 `open_question` 으로.
- **그래픽/사운드 자체의 분석** — 자극 파일 (.png, .wav, .mp4) 의 픽셀 / 주파수 내용은 보지 않습니다. 자극 이름·크기·경로만 기록.

---

## 어떻게 만들어졌나 — 출처

이 플러그인은 두 단계로 다듬어졌습니다:

1. **CSNL 내부 컨벤션 조사** ([`db/csnl-conventions.json`](./db/csnl-conventions.json)). 10명 연구자의 `/Memory/<initial>/` 트리를 10개의 격리된 read-only Explore 서브에이전트로 병렬 답사. 각 연구자의 실험-진행 코드 vs 분석 코드 구분, 프레임워크 분포, schedule pattern 분류, 명명 규칙, 한국어 → 영어 매핑 — 모두 lens 의 inductive bias 가 됨.

2. **외부 prominent labs 메타서치** ([`db/external-samples.json`](./db/external-samples.json)). 5개의 격리된 Opus 서브에이전트가 GitHub 공개 organization + OSF deposit + 랩 사이트 supplementary 를 답사 — Gardner / Acerbi / Stocker / Sims / Brainard·Wichmann·Ma·Gold·Pelli·Wandell. shallow clone 후 entry 파일 + README 읽고 33 샘플 카탈로그화. 각 샘플마다 `framework`, `schedule_mechanism`, `adaptive`, `factors[]`, `saved_variables`, `conventions[]`, `evidence (file:line)` 기록.

전체 출처 (orchestrator 모델, 5개 agent ID, shallow-clone 된 `/tmp/` 트리, GitHub 등 canonical upstream URL, per-agent tool-call 카운트) 는 `db/external-samples.json` 의 `_meta.provenance` 와 [`db/external-samples-summary.md`](./db/external-samples-summary.md) 의 Provenance 절에 명시. 재현 recipe 는 [`scripts/scan-csnl-conventions.md`](./scripts/scan-csnl-conventions.md) (내부) 와 [`scripts/scan-external-samples.md`](./scripts/scan-external-samples.md) (외부).

---

## Changelog

### v0.2.0 (mgl + PsychoJS Builder + adaptive + external-host + 33-sample DB)

두 개의 병렬 Opus 에이전트 harness (5 로컬 deep-uncertainty + 5 외부 메타서치) 가 33 샘플을 카탈로그화 → v0.2 lens 보강에 반영.

**렌즈 변경**

- `prompts/lenses/mgl.md` (NEW) — Justin Gardner 의 MATLAB OpenGL 프레임워크 전용 렌즈. 3-mode 분류 (callback / primitive / hybrid), `task.parameter` vs `randVars` vs `expBlock.*Seq` 인 3원 factor 추출, `mgl-hybrid` (HJL Main_RingExp 의 entry 는 primitive 인데 framework 파일이 같은 디렉토리에 공존하는 경우) 처리.
- `prompts/lenses/psychopy.md` 확장 § 5 (PsychoJS Builder export) — 4-파일 fingerprint + **Scheduler-graph 시그널 필수** (≥3 of `flowScheduler.add` cascade, `RoutineBegin` boilerplate, `nextEntry(snapshot)` advance pattern, started/stopped auto-telemetry). 네 파일이 있어도 Scheduler graph 가 없으면 `psychojs-handwritten`. Routine triple grouping, xlsx factor typing (`nunique` 기반), config-as-conditions 트릭 인식.
- `prompts/lenses/psychtoolbox.md` 확장 — staircase / Quest / Quest+ / PSI / Bayesian adaptive 적응형 절차 절 + 외부 호스팅 패턴 절.

**Anatomist 에이전트**

- Pass 2: lens loading 을 Read-tool 호출로 명시 ("Read `${CLAUDE_PLUGIN_ROOT}/prompts/lenses/<x>.md` verbatim into context BEFORE running Passes 3-7").
- Pass 4: factors-live-in-multiple-places 규칙을 framework 별 체크리스트로 명시. 미해결 adaptive rule 의 hard-rule fallback (`update_rule=null` + `rule_confidence="low"` + `open_question`).
- Pass 10: ADAPTIVE_REPLAYABLE auto-credit (per_trial_state_saved 가 non-empty 면 randomization 만점).
- External detector: positive URL evidence 요구 (small pilot 의 false-positive 방지).
- Korean summary 템플릿에 adaptive_procedure + external_host 항목 추가.
- 내부 플래그 (SCHEDULE_ACTIVE / MGL_PREBUILT_SEQUENCE_ACTIVE) 출력 금지 명시.

**Schema 1.0.0 → 1.1.0** (additive, backward-compatible)

- `platform.framework` enum + mgl, psychojs, psychojs-builder, psychojs-handwritten, external.
- `platform.variant` (free-form 서브모드).
- `platform.runtimes[]` (Builder dual-export 대비).
- `platform.external_host { kind, url, evidence }`.
- 루트 `adaptive_procedure { family, engine, update_rule, rule_confidence, n_interleaved, interleaving_key, termination, per_trial_state_saved, warm_start, evidence }`.

**Codex 어드버서리얼 리뷰** — 7 CRITICAL + 5 MEDIUM 이슈 ship 전 해소. 자세한 issue → fix 매핑은 위 변경 내역 참고.

**새 DB** — `db/external-samples.json` (33 샘플), `db/external-samples-summary.md`, `scripts/scan-external-samples.md`. 출처 (orchestrator 모델, 5 agent ID, `/tmp/` 클론 트리, canonical upstream URL, tool-call 카운트) 명시.

### v0.1.1 (interview-driven hardening)

실제 실험 correctness 리뷰 기반:

- **PTB 렌즈 — "Pre-generated schedule" 패턴 1급 처리**: `load(*schedule*.mat)` AND `(make|generate|build|prep|seed)_?.*(schedule|trial).*\.m` 생성기 동시 존재 시 활성. 이때 `factor.level_source="inline-literal"`, `randomization.scheme="fixed_schedule"`, FULL seed credit (gold-standard reproducibility).
- **Within-subject vs between-subject counterbalance**: 분류는 generator 가 `(subj, day)` per 로 iterate 하는지 (within) `subj` only 인지 (between) 로. schedule `.mat` 은 resolved mapping 만 저장하고 scheme 자체는 generator code 에 있음.
- **Anatomist 패스 3/4/5/10 업데이트** — schedule pattern detect, generator 를 번들에 끌어옴, `design_matrix_summary` 를 generator 소스에서 도출, 활성 시 seed/randomization 자동 만점.
- **Hard rule 강화 — "No invention"**: `n_blocks`, `n_trials_per_block`, `total_trials_estimate`, level 값을 source 의 literal 에서 읽거나 `null` + `open_questions[]`. Intuition 이나 sibling experiment 에서 절대 채우지 않음.
- **New static check `schedule_consistency`**: schedule 패턴 활성 시 literal block/trial constant 가 schedule cell-array 차원과 일치해야 함. 불일치 → open_question.
- **Example corrected**: `examples/timeexp2-example.json` 이 실제 TimeExp2 구조 (within-subject CB dist, pre-gen schedule + scheduleRngState, illustrative-marker on counts) 를 반영.

### v0.1.0

Initial release.

---

## 관련 리소스

- [docs/getting-started.md](./docs/getting-started.md) — 5분 안에 첫 분석 돌리기
- [docs/output-fields.md](./docs/output-fields.md) — JSON 각 필드 한국어 해설
- [docs/by-framework.md](./docs/by-framework.md) — PTB / mgl / PsychoPy / PsychoJS Builder / jsPsych 별 가이드 + 함정
- [docs/interview-mode.md](./docs/interview-mode.md) — 인터뷰가 어떻게 작동하는지, 어떻게 push back 하는지
- [docs/reproducibility-and-rigor.md](./docs/reproducibility-and-rigor.md) — 점수 채점 기준
- [docs/faq.md](./docs/faq.md) — 자주 묻는 질문 (확장판)
- [INSTALL.md](./INSTALL.md) — 설치 + 트러블슈팅
- [`schemas/experiment-spec.schema.json`](./schemas/experiment-spec.schema.json) — 출력 JSON 의 정확한 스키마 (validation 가능)
- [`schemas/postgres-mapping.md`](./schemas/postgres-mapping.md) — PostgreSQL DDL + upsert 흐름
- [`db/csnl-conventions.json`](./db/csnl-conventions.json) + [`db/conventions-summary.md`](./db/conventions-summary.md) — CSNL 10명 컨벤션 DB
- [`db/external-samples.json`](./db/external-samples.json) + [`db/external-samples-summary.md`](./db/external-samples-summary.md) — Gardner/Acerbi/Stocker/Sims/인접 10랩 33샘플 외부 DB
- `csnl-archive` 플러그인 — 같은 grounded-interview methodology 로 *프로젝트 단위* archive 를 만드는 자매 플러그인 (per-experiment 가 아닌 per-project 레벨).

## License

MIT. See [LICENSE](./LICENSE).
