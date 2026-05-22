# 자주 묻는 질문 (FAQ)

README 의 짧은 FAQ 를 확장한 버전. 실제 연구자들이 묻는 질문 위주.

## 사용 흐름

### Q. 처음인데 뭐부터 시작?
A. [getting-started.md](./getting-started.md) — 5분 안에 첫 분석 돌리는 walkthrough.

### Q. 내 실험은 PsychoPy Builder 인데 .py 와 .js 가 모두 나온다. 어느 쪽이 source of truth?
A. `.psyexp` (XML 원본) 을 **구조 (factors, loops, conditions)** 의 ground truth 로, `.js` 를 **runtime 사이드이펙트 / 데이터 캡처** 의 ground truth 로 봅니다. `platform.runtimes = ["python-desktop", "javascript-web"]` 으로 양쪽 모두 기록.

### Q. 같은 실험을 여러 번 분석하면 결과가 같나?
A. 거의 같지만 — Opus 의 자유 텍스트 필드 (`identity.summary`, `score.notes`, `design_matrix_summary`) 는 약간 달라질 수 있습니다. 하지만 **structured field 들** (factors[], parameters[], saved_variables[]) 은 evidence (file:line) 기반이라 deterministic 에 가깝습니다. 같은 코드에서 factor 개수가 5개에서 7개로 바뀌면 — 그건 lens 가 못 잡던 것을 새로 잡았거나, 첫 분석에서 over-extract 했다는 신호.

### Q. 결과 JSON 을 사람이 직접 손으로 고쳐도 되나?
A. 됩니다. schema 검증만 통과하면 (`schemas/experiment-spec.schema.json`). 자주 손으로 고치는 경우:
- `identity.summary` 를 더 매끄러운 한국어로
- `design_matrix_summary` 를 verbose 하게 풀어쓰기
- 인터뷰에서 못 잡은 `open_questions[]` 답을 manually 채우기
`/experiment-anatomy:review` 가 수동 편집 → 재검증 사이클을 도와줍니다.

### Q. 인터뷰가 너무 길다.
A. `INTERVIEW=off` 로 호출하면 인터뷰 없이 모든 unresolved 가 `open_questions[]` 로 출력. 나중에 `/experiment-anatomy:review` 로 한 번에. 자세히는 [interview-mode.md](./interview-mode.md) § "인터뷰를 건너뛰고 싶을 때".

### Q. Pass 12 가 안 나오고 바로 끝났다.
A. 세 가지 가능성:
1. 모든 정보가 코드에 있음 (가장 깨끗한 경우).
2. `INTERVIEW=off` 가 켜져 있음.
3. Anatomist 가 추측해서 채워버렸을 가능성 — JSON 의 `evidence` 가 모두 `file:line` 또는 `interview:` prefix 인지 확인.

### Q. 어떻게 batch (여러 실험 한꺼번에) 돌리나?
A.
```bash
for exp in TimeExp1 TimeExp2 RingExp; do
  /experiment-anatomy:analyze /Volumes/.../$exp INTERVIEW=off RESEARCHER_INIT=JOP SHORT_ID=$exp
  /experiment-anatomy:export ./experiment-spec.json
  mv experiment-spec.json out/${exp}-spec.json
done
```
`INTERVIEW=off` + PostgreSQL upsert 가 batch 모드의 표준.

## 정확도 / 추출 결과 관련

### Q. 내 factor 가 안 잡혔다 / 잘못 잡혔다.
A. 흔한 원인:
- **인터뷰에서 push back 해주세요** — "그건 IV 아니야" 또는 "이 변수가 factor 야" 라고 답하면 즉시 spec 에 반영.
- **`MAX_BYTES` 키우기** — 디폴트 400 KB 가 다 안 읽혀서 generator 파일을 못 봤을 수 있음. `MAX_BYTES=1500000` 으로 재호출.
- **명시적 entry / docs 전달** — `ENTRY=src/main.m DOCS=docs/methods.md`.

### Q. n_trials / n_blocks 가 null 로 나왔다.
A. 의도된 동작입니다. **Hard rule 2: "No invention"** — 코드 literal 에서 못 읽으면 절대 추측 안 함. 동시에 `open_questions[]` 에 그 질문이 들어있습니다.
- 정상: 인터뷰에서 답하면 채워짐.
- 비정상 (literal 이 있는데도 못 잡음): bug → issue.

### Q. mgl 실험인데 `framework = "psychtoolbox"` 로 나왔다.
A. mgl primitive + PTB primitive 가 한 파일에 동시 존재 → `ptb-mixed` 로 demote. 또는 `framework_canonical` confusion. 자세히는 [by-framework.md § mgl](./by-framework.md#mgl-justin-gardner--matlab).
임시 대응: `FRAMEWORK_HINT=mgl` 인자 추가 (lens 가 선택을 override).

### Q. PsychoJS Builder export 인데 `psychojs-handwritten` 으로 나왔다.
A. 4-파일 fingerprint 는 있지만 **Scheduler-graph 시그널이 약함**. Builder 가 emit 하는 보일러플레이트 (`flowScheduler.add(...)` cascade, `RoutineBegin` 표준 도입 라인, `nextEntry(snapshot)` advance, started/stopped auto-telemetry) 가 ≥3 개 fire 해야 Builder 확정. 보통 researcher 가 .js 를 manual 편집해서 보일러플레이트를 제거했을 때 이렇게 됩니다.
임시 대응: `.psyexp` 가 명백히 Builder 면 `FRAMEWORK_HINT=psychojs-builder`.

### Q. Adaptive procedure 가 `staircase` 인데 `quest` 로 나왔다.
A. Detection 시그널 충돌 (코드에 `QuestUpdate` 호출은 있지만 실제 `QuestQuantile` 로 next stim 결정 안 함, 또는 staircase 변수를 Quest 라이브러리에 *로깅만* 함). 인터뷰에서 push back:
```
> family 는 quest 가 아니라 1-up-2-down Levitt staircase 야. QuestUpdate 는 historical artifact 일 뿐 — 실제 driver 는 upDownStaircase.
```

### Q. 외부 호스팅 (Pavlovia) 인데 `framework = "unknown"` 으로 나왔다.
A. v0.2 의 false-positive 방지: positive URL evidence (Pavlovia/Gorilla/OSF/GitHub link) 가 README/docs 에 명시되어 있어야 `external` 분류. README 에 URL 한 줄 추가:
```markdown
## Hosting
Task hosted on Pavlovia: https://pavlovia.org/<user>/<exp>
```
또는 `EXTERNAL_HOST=pavlovia URL=https://...` 인자 전달.

### Q. 분석 코드 (.py 로 결과 plot 하는 것) 가 실험-진행 코드로 잘못 잡혔다.
A. 정상적으론 `analysis_exclusion_signatures` 가 자동 제외 (`analyze_*`, `proc_*`, `plot_*` 파일명, `.nii`, `NIfTI`, `SPM`, `FSL`, `AFNI`, `fMRIPrep`, `BIDS`, `mrtools` 참조, EyeLink `.edf` parsing 등). 잘못 통과한 경우 인터뷰에서 push back 또는 `ENTRY=path/to/actual_runner.m` 명시.

## 점수 / 채점 관련

### Q. 재현성 점수가 너무 낮다.
A. [reproducibility-and-rigor.md § 점수가 낮을 때](./reproducibility-and-rigor.md#점수가-낮을-때-무엇을-할까) 의 component-별 action item 참고. 보통 lockfile (`pip freeze > requirements.txt && pip freeze --all > requirements.lock`) 한 번이 +5~10점, Dockerfile 추가가 +10점.

### Q. 엄밀성에서 blinding 이 N/A 인데 0점.
A. 0 점이 아니라 component 가 제외됩니다. `score.overall` 은 다른 5개 (총 85점 만점) 만 합산하고 100점 환산. e.g. 다른 5개에서 75점 → `75/85 × 100 = 88` 점.

### Q. Adaptive procedure 인데 `randomization` 이 partial 로 떨어졌다.
A. `per_trial_state_saved = []` (final estimate 만 저장). staircase 의 `s.response[]` + `s.strength[]` 가 `.mat` 에 들어가는지 확인 — 보통 mgl 의 `endTask` 가 global `stimulus` 를 자동 저장하니까 코드에 explicit save 가 없어도 OK. PTB hand-rolled 면 `save(.., 'staircase')` 호출 추가.

### Q. `schedule_consistency` 가 false 로 나왔다.
A. Pre-generated schedule 패턴 활성 (load `*schedule*.mat` + 생성기 존재) + literal block/trial 카운트 ≠ schedule cell-array 차원. 흔한 원인:
- 생성기를 재실행해서 schedule 차원이 바뀌었는데 entry script 의 literal 은 안 갱신됨
- Entry 의 `nBlocks = 12` 같은 literal 이 사실은 outdated change log

Action: schedule `.mat` 차원이 실제 run 값이고 (loop 가 `1:length(...)` 이라면) literal 을 거기에 맞춰 갱신, 또는 schedule 재생성.

## 외부 lab / fork 관련

### Q. CSNL 외 다른 lab 에서 써도 되나?
A. 네. fork 권장.
- CSNL convention (`par.tp.<channel>` timing, `make_*schedule*.m` 생성기, `participants.csv` 으로 between-subject CB) 가 lens 에 일부 코딩되어 있어서 — 다른 lab 의 패턴과 안 맞으면 `prompts/lenses/*.md` 를 prune/replace.
- PR 환영 — 다른 lab 의 패턴이 lens 에 들어가면 모두에게 이득.

### Q. CSNL 외 lab 에서 fork 했을 때 가장 먼저 손볼 곳?
A.
1. `prompts/lenses/psychtoolbox.md` 의 "Per-trial saved variables" 절 — CSNL 의 `par.tp.<channel>{iR}(iT)` 같은 lab-specific 컨벤션 제거.
2. `db/csnl-conventions.json` 을 자체 lab survey 로 교체 (또는 빈 파일로 시작).
3. `agents/anatomist.md` 의 Hard rule 5 "Korean prose, English keys" 에서 한국어 부분을 자기 언어로.
4. `README.md` 의 "Audience" 절을 자기 lab 으로.

### Q. 우리 lab 은 OpenSesame / E-Prime / Inquisit 인데?
A. v0.2 에서는 `opensesame` / `neurobs-presentation` enum 만 있고 전용 렌즈는 없습니다. generic 렌즈로 처리되어 정확도가 framework-specific 의 70% 정도. 전용 렌즈 PR 환영.

### Q. 우리 lab 의 자체 framework (custom MATLAB toolbox) 인데?
A. `framework = "custom"` 으로 떨어집니다. generic 렌즈로 처리. 정확도를 올리려면:
1. `prompts/lenses/<your-framework>.md` 작성 (PTB lens 베껴서 시작 추천).
2. `agents/anatomist.md` Pass 2 의 framework enum 에 추가.
3. `schemas/experiment-spec.schema.json` 의 `platform.framework` enum 에 추가 (1.2.0 으로 minor bump).

## 운영 / DevOps

### Q. Opus 가 비싸다. 다른 모델로 돌릴 수 있나?
A. `agents/anatomist.md` 의 `model: opus` 프런트매터를 바꾸면 됩니다. 다만 12-pass 의 깊이가 가치 — Sonnet 4.6 까지는 보장하지만 그 아래는 ablate 됩니다. 짧은 코드 (< 50 KB) 면 Sonnet 으로 충분.

### Q. 매번 인터뷰가 같은 걸 묻는다.
A. 인터뷰 답이 spec 에 반영되어도 — **다음 분석 (다른 실험)** 에는 carry-over 안 됩니다. lab-wide pattern (e.g. "우리 lab 은 항상 par.subID 가 subject ID") 같은 건 `prompts/lenses/*.md` 에 박아넣는 게 답.

### Q. PostgreSQL 적재가 실패한다.
A. `python3 scripts/upsert-to-postgres.py ./experiment-spec.json --dry-run` 으로 SQL 확인. 흔한 원인:
- DDL 미적용 → `schemas/postgres-mapping.md` 의 7개 `CREATE TABLE` 다시.
- `DATABASE_URL` 환경변수 미설정.
- short_id 가 null → unique constraint 위반. `SHORT_ID=...` 명시.

### Q. 분석 결과가 SMB 마운트 경로를 그대로 박아둔다.
A. 의도된 동작입니다. `/Volumes/CSNL_new-1/...` 가 그대로 들어있는 것 자체가 reproducibility 정보 — "이 데이터는 lab SMB share 의 이 경로에 있다". `deterministic_paths` 점수에는 영향 — 절대 경로가 많을수록 점수 낮음. 상대 경로 (`./data/<subID>/`) 로 바꾸는 게 best practice.

### Q. .vercel / .next / node_modules 같은 게 file count 에 잡힌다.
A. 디폴트로 다음 패턴 제외:
- `node_modules/`, `.git/`, `.vercel/`, `.next/`, `dist/`, `build/`, `*.egg-info/`, `__pycache__/`, `*.pyc`
- `*.svn-base`, `*~`, `*orig.m`, `*.asv`
- `*_backup_*`, `archive/`, `Old_*`, `legacy/`, `deprecated/`
- `*-legacy-browsers.js` (PsychoJS Builder fallback — note 만 하고 deep-read 안 함)

추가로 제외하고 싶으면 `EXCLUDE=path1,path2` 인자.

### Q. 분석 도중 멈췄다.
A. Claude Code 세션을 다시 열고 `/experiment-anatomy:analyze ./` 재실행. 결과는 어디에도 cache 되지 않으니 — 클린 재실행. 길이 (12 pass, 보통 5–15분) 가 부담이면 `INTERVIEW=off` 로 batch 모드.

## 개발 / 기여

### Q. lens / agent / schema 를 어떻게 고치나?
A. fork → 수정 → PR. 변경한 부분에 대한 evidence (real lab code 또는 실험 결과) 함께 첨부 권장. lens 변경은 `db/csnl-conventions.json` 또는 `db/external-samples.json` 의 새 row 와 함께 오면 가장 잘 받아들여집니다.

### Q. Codex / Opus 같은 추가 모델로 review 한 결과를 PR 에 함께 넣어도 되나?
A. 환영. 우리도 v0.2 에서 Codex adversarial review (7 CRITICAL + 5 MEDIUM 잡힘) 거쳐서 ship. lens 변경이 lab 코드에 안 맞는지 (false-positive / false-negative) 확인하는 다른 시각이 도움됨.

### Q. 새 lab / 새 framework 데이터를 어떻게 추가하나?
A. [`scripts/scan-csnl-conventions.md`](../scripts/scan-csnl-conventions.md) (lab-internal) 또는 [`scripts/scan-external-samples.md`](../scripts/scan-external-samples.md) (외부 GitHub/OSF) 의 harness recipe 따라 → 결과 JSON row 를 `db/*-samples.json` 에 추가 → 새 패턴이 발견되면 `prompts/lenses/*.md` 에 룰 추가 → PR.

## 알려진 이슈

### Q. v0.1.x spec 으로 적재된 DB row 가 v0.2 schema 와 호환되나?
A. 네, schema 1.0.0 → 1.1.0 은 additive (모든 새 필드 optional). v0.1.x spec 도 1.1.0 schema validation 통과. PostgreSQL row 도 그대로.

### Q. v0.2 의 새 필드 (`adaptive_procedure`, `platform.runtimes[]`, `platform.external_host`) 가 DB 의 어디에 들어가나?
A. `experiment_specs` 메인 테이블의 `spec_json` 컬럼에 그대로. 별도 child table 은 v0.3 에서. v0.2 까지는 jsonb path 쿼리로 접근:
```sql
SELECT identity->>'short_id', adaptive_procedure->>'family'
FROM experiment_specs
WHERE adaptive_procedure IS NOT NULL;
```

### Q. windows 에서 돌리려면?
A. WSL2 안에서. native Windows 는 미테스트.

### Q. lens 가 일본어 코드 / 중국어 코드 / 한국어 (변수명) 코드를 다루나?
A. 코드 자체는 식별자 (변수명) 가 어느 언어든 처리. Free-form text (한국어 README, 중국어 코멘트) 도 Opus 가 native 처리. lens 자체는 영어로 작성되어 있지만 매칭은 unicode aware.

### Q. lens 가 잘못된 detection 을 하면 어떻게 신고?
A. Issue 에 (i) 코드 snippet (또는 redacted), (ii) `experiment-spec.json` (또는 redacted), (iii) 무엇이 잘못됐는지, (iv) 기대한 결과. real code 예시가 가장 잘 받아들여집니다.

---

## 더 묻고 싶은 게 있다면

[GitHub Issues](https://github.com/CSNL-vnilab/experiment-anatomy/issues) 에 올려주세요. lab member 면 Slack #ai-tools 채널.
