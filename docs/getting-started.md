# 시작하기 — 5분 안에 첫 분석

실험자 입장에서, **내 코드를 한 번 분석해보고 결과 JSON 을 받아보는** 가장 빠른 경로입니다.

## 사전 준비

- macOS 또는 Linux (Windows 는 WSL2)
- Claude Code CLI 설치 ([claude.ai/code](https://claude.ai/code))
- 분석하고 싶은 실험 코드 폴더 (로컬 또는 SMB 마운트)

## 1. 플러그인 설치 — 한 번만

Claude Code 세션을 열고:

```
/plugin marketplace add CSNL-vnilab/experiment-anatomy
/plugin install experiment-anatomy@experiment-anatomy-marketplace
```

세션을 재시작하면 다음 슬래시 커맨드가 보입니다:

- `/experiment-anatomy:analyze` — 실험 분석
- `/experiment-anatomy:review` — 인터뷰 답변 후 spec 재유도
- `/experiment-anatomy:export` — PostgreSQL 에 업서트

## 2. 분석 돌리기

실험 폴더로 `cd` 한 다음:

```
/experiment-anatomy:analyze
```

또는 경로를 인자로:

```
/experiment-anatomy:analyze /Volumes/CSNL_new-1/people/JOP/Magnitude/Experiment/Time2Dist
```

옵션 (선택):

| 인자 | 의미 |
|---|---|
| `SHORT_ID=TimeExp2` | spec.json 의 자연 키 (없으면 인터뷰에서 물음) |
| `PARADIGM_GENRE=estimation` | 장르 hint (psychophysics / estimation / decision / retrieval / search / perception / memory / motor / categorization / attention / imagery / language / social / gamified / other) |
| `RESEARCHER_INIT=JOP` | provenance.researcher_initial — 누가 분석을 돌렸는지 |
| `INTERVIEW=off` | Pass 12 인터뷰 스킵 → 모든 unresolved question 이 `open_questions[]` 로 출력 |
| `MAX_BYTES=1500000` | 읽기 상한 (디폴트 400 KB; 큰 repo 면 키우기) |
| `DOCS=docs/protocol.md` | 추가로 읽어야 할 README 외 문서 경로 (콤마 구분 가능) |

## 3. 진행 보기

Anatomist 가 12 pass 를 차례로 돌립니다. 각 pass 시작 시 한 줄씩 progress 출력:

```
✦ Pass 1 — 트리 훑기 (47개 파일, 280KB 읽음)
✦ Pass 2 — 플랫폼: psychtoolbox (변형 없음), confidence 0.97
✦ Pass 3 — 계층 구성 중...
...
✦ Pass 12 — 확인 인터뷰 (질문 2개)
```

Pass 12 인터뷰가 시작되면 한국어로 질문이 떠 — 한 번에 하나, 코드 라인 근거 + 4지선다.

```
Q1 (factors):
  par.exclude.rt_min = 0.2 (analyze.m:34) — 이 값이…
  ① 분석 단계 제외 기준
  ② 실험 진행 중 제외 기준
  ③ 둘 다
  ④ 건너뜀 / 모름
>
```

답을 입력하면 spec 에 반영하고 다음 질문으로. 종료 조건: 모든 material question 풀림 / "그만"·"skip"·"나중에" 입력 / 10개 질문 도달.

## 4. 결과 확인

현재 디렉토리에 두 파일이 생깁니다:

```
./experiment-spec.json         # 표준 JSON (스키마 1.1.0 통과)
./experiment-spec-summary.md   # 한국어 80줄 요약
```

요약 마크다운을 먼저 보면 됩니다:

```bash
$ cat experiment-spec-summary.md

# TimeExp2 — 분석 결과 요약

**한 줄**: Duration discrimination 시간 추정 실험 · estimation 장르 · MATLAB + Psychtoolbox (pre-generated schedule 패턴)

**계층**: session: par.day 1..5 (within_subject); block: nBlocks=12; trial: nT=40 → 총 2400 trials/subj

**조작변수 (3개)**:
- dist (within_subject, 2 levels): short / long — make_trial_schedule_duration.m:18 에서 day-by-day 로 counterbalance
- day (within_subject, 5 levels): 1..5 — main_duration.m:24
- tprecue (per_trial, continuous): make_trial_schedule_duration.m:45 에서 [0.3, 0.5] 균등 샘플

**파라미터 41개, 저장변수 28개, 디스플레이 5개, 저장경로 2개** (자세한 내역은 spec.json)

**적응형 절차**: constant-stimuli (적응형 없음)

**재현성 92/100**:
- seed: 25/25 (pre-generated schedule, scheduleRngState 저장됨 — gold standard)
- randomization: 15/15 (fixed_schedule)
- version_pinning: 12/25 (MATLAB 만 documented, PTB 버전 unpinned)
- env_capture: 20/20 (requirements.m 존재)
- deterministic_paths: 20/15 — wait, max 15 → 15/15 (subID + day 들어간 경로)

**엄밀성 78/100**:
- counterbalancing: 25/25 (declared + symmetric)
- sample_size: 8/20 (ad_hoc — N=20 명, no power analysis)
- blinding: applicable + present (15/15)
- preregistration: 0/10 (no OSF link)
- exclusion_rules: 15/15 (RT < 200ms + accuracy floor 모두 코드 + docs)
- checks: 15/15 (all 5 boolean checks pass)

**다음 단계**:
1. (rigor) preregistration URL 이 있다면 docs/protocol.md 에 추가하시면 점수 + 10
2. (parameters) par.feedback_duration_ms 가 코드에는 안 보이는데 README 에 있음 — 어디서?
3. 확인 완료
```

## 5. PostgreSQL 에 적재 (선택)

랩 DB 가 준비됐다면:

```
/experiment-anatomy:export ./experiment-spec.json
```

DDL 적용·DATABASE_URL 설정은 [INSTALL.md](../INSTALL.md) § 2-3 참고.

## 자주 막히는 곳

**"경로를 찾을 수 없습니다"**
SMB 마운트 (`/Volumes/CSNL_new-1/...`) 가 해제됐을 수 있음. Finder 에서 다시 connect 후 재시도. 또는 로컬 경로를 직접 전달.

**Pass 1 에서 "no candidate entry files found"**
`main_*`, `run_*`, `experiment*.py`, `index.{js,ts,html}`, `app.{js,py}` 패턴이 없는 경우. `DOCS=path/to/readme.md` 로 README 경로를 명시적으로 전달.

**Pass 2 가 `framework = "unknown"`**
플랫폼이 enum 에 없거나 (E-Prime, Inquisit 등) 너무 minimal 한 custom 코드. `platform`-topic open_question 이 1개 자동 생성됩니다 — 답하면 generic 렌즈로 계속 진행.

**Pass 12 가 너무 많이 묻는다**
`INTERVIEW=off` 로 호출하면 인터뷰 없이 모든 unresolved 가 `open_questions[]` 에 들어갑니다. 나중에 `/experiment-anatomy:review` 로 한 번에 답변 가능.

**결과 JSON 이 비어 보인다**
첫 pass 에서 entry 가 잘못 잡혔을 가능성. `experiment-spec-summary.md` 의 "한 줄" 줄을 보고 — 엉뚱한 파일을 골랐다면 다시 호출하면서 entry 파일을 직접 인자로 전달: `/experiment-anatomy:analyze /path/ ENTRY=src/main.m`.

## 다음 단계

- 출력 JSON 의 각 필드 의미: [output-fields.md](./output-fields.md)
- 내 플랫폼별 함정: [by-framework.md](./by-framework.md)
- 인터뷰 모드 자세히: [interview-mode.md](./interview-mode.md)
- 재현성·엄밀성 점수 기준: [reproducibility-and-rigor.md](./reproducibility-and-rigor.md)
- FAQ: [faq.md](./faq.md)
