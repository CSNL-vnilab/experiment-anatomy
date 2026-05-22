# 재현성과 엄밀성 점수 — 무엇이, 어떻게 채점되나

`reproducibility.score.overall` 과 `rigor.score.overall` — 둘 다 0–100점. 한 줄짜리 verdict 가 아니라 **각 component 가 왜 그 점수인지 코드 라인 근거** 와 함께 나옵니다.

논문 리뷰어가 묻기 전에 스스로 확인할 수 있도록.

## 재현성 (Reproducibility) — 100점

**"제 3자가 이 코드 + .mat / .csv 데이터를 받았을 때, 같은 숫자를 얻을 수 있나?"**

5개 component 합산:

| Component | 만점 | 만점 조건 |
|---|---|---|
| `seed` | 25 | RNG seed 가 deterministic source (subject ID, 등) 에서 pin |
| `randomization` | 15 | scheme 이 declared 되어 있고 코드와 일치 |
| `version_pinning` | 25 | 모든 declared dependency 가 pinned (lockfile 존재) |
| `env_capture` | 20 | environment 가 captured (lockfile / requirements / Dockerfile) |
| `deterministic_paths` | 15 | data path 가 `<subID>` / `<date>` / iteration counter 같은 deterministic placeholder 사용 |

### Component 1: `seed` (25점)

| 시나리오 | 점수 |
|---|---|
| Deterministic source — `rng(subjNum * day)`, `np.random.seed(int(expInfo['participant']))` | **25** |
| **CSNL pre-generated schedule 패턴 활성** + `par.scheduleRngState` 가 saved → 자동 25 | **25 (자동 gold standard)** |
| **Two-stage seed** (HJL: `expData.seedRand = ceil(rand(1)*10000); rand('state', seedRand)`) — 풀린 seed 가 `expData.seedRand` 에 저장됨 | **25** (saved 면) |
| `time.time()` / `os.clock()` 에서 draw — pinned 되었지만 비-결정적 | **15** |
| `'shuffle'` / `numpy.random.seed(None)` 가 documented | **5** |
| 미설정 (default RNG, 그대로 사용) | **0** |

### Component 2: `randomization` (15점)

| Scheme | 점수 | 의미 |
|---|---|---|
| `fixed_schedule` | **15** | pre-generated `.mat` 또는 deterministic generator |
| `block_shuffle`, `trial_shuffle`, `counterbalanced`, `latin_square` | **15** | scheme 이 declared + 코드와 일치 |
| **Adaptive procedure + `per_trial_state_saved` 가 non-empty** | **15 (자동)** | trajectory 가 replayable — 자세히 아래 |
| `adaptive` 만 declared, state 안 저장 | **8** | final estimate 만 보존 |
| `ad_hoc` (declared 안 됨, 그러나 reproducible) | **8** | |
| `none` / `unknown` | **0** | |

#### `ADAPTIVE_REPLAYABLE` 자동 만점 조건

Family 별로:

| Family | replay 가능 조건 |
|---|---|
| `staircase` | `s.response[]` + `s.strength[]` + init params 저장 |
| `quest` / `quest_plus` | `intensity[]` + `response[]` (또는 full posterior history) |
| `psi_kontsevich_tyler` | `psy` 구조체 (posterior over μ,σ,λ + trial history) saved |
| `bayesian_adaptive` | per-trial posterior summary 또는 full particle/grid snapshot (`Theta{i_tr}`) |

위 조건 만족 시 `randomization` 자동 15/15 + `score.notes` 에 "ADAPTIVE_REPLAYABLE 자동 만점" 메모. `per_trial_state_saved = []` (final 만 저장) 이면 partial (8/15).

### Component 3: `version_pinning` (25점)

`platform.external_dependencies[]` 의 `pinned=true` 비율 × 25, round down.

```
pinned: 6, total: 8 → 6/8 × 25 = 18 (round down) → 18
```

`total = 0` (declared deps 없음) → 0.

Lockfile (`package-lock.json`, `yarn.lock`, `requirements.lock`, `poetry.lock`, `renv.lock`, `Manifest.toml`, `Gemfile.lock`) 있으면 `lockfile_present: true`.

### Component 4: `env_capture` (20점)

| `completeness` | 점수 | 의미 |
|---|---|---|
| `full` | **20** | Lockfile 있음 또는 Docker/Nix flake |
| `partial` | **10** | `requirements.txt` / `environment.yml` 은 있지만 lock 없음 |
| `absent` | **0** | 아무것도 없음 |

`files_found[]` 에 실제 발견된 파일명 (`requirements.txt`, `pyproject.toml`, `package-lock.json`, `Dockerfile`, `flake.lock`, 등).

### Component 5: `deterministic_paths` (15점)

`storage.data_paths[]` 의 path string 분석:

- `<subID>` / `<date>` / `<expName>` / iteration counter 형식 placeholder + 상대 경로 → **15**
- 부분적으로 deterministic 하지만 hard-coded 절대 경로 일부 (`/Users/csnl/Desktop/...`) 섞임 → **8**
- 모두 hard-coded 절대 경로 (재현 불가능) → **0**

### `notes` 필드

특수 케이스가 있을 때 anatomist 가 짧게 메모:

```
"notes": "SCHEDULE_ACTIVE 패턴 — gold standard reproducibility (seed + randomization 자동 만점). version_pinning 12/25: MATLAB 만 documented, PTB 버전 unpinned. Docker 사용 권장."
```

---

## 엄밀성 (Rigor) — 100점

**"이 실험이 방법론적으로 견고한가?"**

6개 component 합산:

| Component | 만점 | 만점 조건 |
|---|---|---|
| `counterbalancing` | 25 | scheme 이 declared + IV 가 symmetric 하게 counterbalanced |
| `sample_size_justification` | 20 | power analysis 또는 precedent + citation |
| `blinding` | 15 | applicable + present (single-subject within-subject 면 N/A → 0이지만 감점 아님) |
| `preregistration_marker` | 10 | OSF / AsPredicted URL 또는 ID |
| `exclusion_rules` | 15 | RT / accuracy / missing-response 규칙이 코드 + docs 모두에 있음 |
| `checks` | 15 | 5개 boolean static check 모두 pass (pro-rated otherwise) |

### Component 1: `counterbalancing` (25점)

| 시나리오 | 점수 |
|---|---|
| Scheme declared + symmetric (모든 condition 이 똑같이 등장) | **25** |
| Declared 부분만 (e.g. between-subject 만, within-subject 빠짐) | **10** |
| 없음 (`present: false`) | **0** |

Pre-generated schedule 패턴 활성 시 — generator (`make_*schedule*.m`) 의 outer loop 가 자동으로 within vs between 으로 분류되고 `scheme` 자유 텍스트로 verbatim 기록.

### Component 2: `sample_size_justification` (20점)

| `method` | 점수 |
|---|---|
| `power_analysis` (G*Power / pwr / statsmodels.power) | **20** |
| `precedent` + 참조 (Acerbi 2014 N=20 같은 citation) | **15** |
| `ad_hoc` (정당화 없이 N 만) | **8** |
| `unstated` / `other` | **0** |

### Component 3: `blinding` (15점)

| 시나리오 | 점수 |
|---|---|
| Applicable + experimenter + participant 둘 다 blind | **15** |
| Applicable + 하나만 blind | **10** |
| Applicable + 없음 | **0** |
| Not applicable (single-subject within-subject 등) | **0 (감점 아님 — note 필요)** |

`blinding.note` 에 적용 가능성 평가:

```json
"blinding": { "applicable": false, "experimenter_blind": null, "participant_blind": null, "note": "Single-subject within-subject design — blinding 불필요" }
```

### Component 4: `preregistration_marker` (10점)

OSF URL (`osf.io/<id>`) 또는 AsPredicted URL/ID 가 docs/code 에 있으면 10, 아니면 0.

### Component 5: `exclusion_rules` (15점)

| 시나리오 | 점수 |
|---|---|
| 코드 (`if rt < 0.2 → skip`) AND docs (README 에 "RT < 200ms 제외") 모두 | **15** |
| 코드만 (docs 미언급) | **8** |
| Docs 만 (코드 미구현) | **0** (논문에는 있는데 실제로는 안 함 — 위험 신호) |
| 둘 다 없음 | **0** |

### Component 6: `checks` (15점)

5개 boolean static check, 모두 pass 면 15, partial 은 비례:

| Check | Pass 조건 |
|---|---|
| `every_factor_has_role` | 모든 factor 에 `role` 채워짐 |
| `no_single_value_factor` | `levels.length ≤ 1` 인 factor 가 없음 (있으면 derived/constant 일 가능성) |
| `saved_5_categories_present` | 5개 scale × 9 category 중 최소 5개 있음 (per_trial × stimulus + response + timing 등) |
| `hierarchy_complete` | session × phase × block × trial 카운트가 모두 채워짐 |
| `no_dead_branches_in_conditions` | conditions[] 의 factor_assignments 가 factors[] 의 levels 와 일치 |
| `schedule_consistency` | (pre-generated schedule 활성 시만) literal block/trial 상수 = schedule cell-array 차원 |

`schedule_consistency` 는 활성 시만 검사 — 비활성 시 omit (0/15 가 아님).

5 → 15, 4 → 12, 3 → 9, 2 → 6, 1 → 3, 0 → 0.

---

## 점수가 낮을 때 무엇을 할까

낮은 점수는 verdict 가 아닙니다 — **action item**:

### 재현성 80 미만이면

| Component 낮음 | 조치 |
|---|---|
| `seed` (< 25) | `rng(subjNum)` 또는 `np.random.seed(int(expInfo['participant']))` 추가. 가능하면 pre-generated schedule 패턴 도입. |
| `randomization` (< 15) | scheme 을 explicit 하게 declare. adaptive 면 `per_trial_state_saved` 채우기. |
| `version_pinning` (< 20) | `pip freeze > requirements.txt` (Python), `npm shrinkwrap` (Node), `renv::snapshot()` (R), `Pkg.instantiate; Pkg.status` (Julia). |
| `env_capture` (< 20) | Dockerfile 추가 또는 `conda env export > environment.yml`. |
| `deterministic_paths` (< 15) | hard-coded `/Users/csnl/Desktop/...` 같은 경로를 `./data/<subID>/<date>/` 로 바꿈. |

### 엄밀성 70 미만이면

| Component 낮음 | 조치 |
|---|---|
| `counterbalancing` (< 25) | scheme 을 docs 에 explicit 하게 명시. counterbalance generator 가 IV 를 symmetric 하게 다루는지 verify. |
| `sample_size_justification` (< 15) | G*Power 또는 pwr 같은 power analysis 돌리고 `docs/sample_size.md` 작성. 또는 precedent citation. |
| `blinding` (< 10) | applicable 한데 미구현이면 — review 시 risk. note 에 사유 명시. |
| `preregistration_marker` (< 10) | OSF preregistration ([osf.io/prereg](https://osf.io/prereg)) 또는 AsPredicted ([aspredicted.org](https://aspredicted.org)). |
| `exclusion_rules` (< 15) | 코드와 docs 양쪽에 동일하게 명시. "분석 단계에서 RT < 200ms 제외" 한 줄이라도. |
| `checks` (< 15) | 어느 check 가 fail 했는지 보고 — 보통 `no_single_value_factor` 이면 derived 한 factor 가 IV 로 잘못 들어가 있음. |

---

## "내 점수가 너무 가혹한데?"

흔한 경우:

**"우리 랩 PTB 버전은 다들 알아서 — pinning 점수가 낮게 나옴"**
→ 그게 정확히 reproducibility risk. 같은 PTB 버전을 명시하지 않으면 5년 뒤 누가 재현할 때 같은 결과가 안 나올 수 있음. `setup_environment.m` 에 `disp(Screen('Version'))` 한 줄 + git tag 하나면 점수 회복.

**"adaptive procedure 인데 randomization 이 partial 로 떨어짐"**
→ `per_trial_state_saved` 가 빈 배열일 때. staircase 의 `s.response[]` + `s.strength[]` 가 `.mat` 에 들어가는지 확인. mgl 의 `endTask` 가 global `stimulus` 저장하는지 — `taskTemplateStaircase.m` 같은 framework 파일을 보면 보통 자동.

**"sample size 가 8/20 으로 자꾸 깎임"**
→ `ad_hoc` 분류. `precedent` 로 올리려면 docs 어딘가에 한 줄: "N=20 (Acerbi et al. 2014 Table 1 기준)". Citation 한 줄이 7점 차이.

**"blinding 이 N/A 인데 0 점 나옴"**
→ N/A 면 감점이 아니라 component 가 빠질 뿐. `score.overall` 은 다른 5개 component (총 85점 만점) 만 합산하고 그 비율을 100점 환산. e.g. 다른 5개에서 75점 → `75/85 × 100 = 88` 점.

---

## 점수 vs 자유 텍스트 notes

점수만 보지 마세요. `score.notes` 가 더 정보적입니다:

```json
"score": {
  "overall": 78,
  "notes": "Counterbalancing 25/25 (within-subject CB declared + symmetric). Sample size 8/20 (ad_hoc — N=20 명, no power analysis). Blinding N/A (single-subject within-subject — single-blind 도 단순화 위해 미적용). Preregistration 0/10 (OSF link 없음 — 추가 권장). Exclusion rules 15/15 (RT < 200ms + accuracy floor 모두 code 와 docs). Checks 15/15 (schedule_consistency 자동 통과)."
}
```

이게 논문 메소드 섹션 또는 reviewer rebuttal 의 raw material 입니다.

---

## 점수를 lab DB 에 적재한 후 query

```sql
-- 재현성 80 이상 실험들
SELECT identity->>'short_id', reproducibility->'score'->>'overall'
FROM experiment_specs
WHERE (reproducibility->'score'->>'overall')::int >= 80;

-- env_capture 가 absent 인 실험들 (action item 큐)
SELECT identity->>'short_id', provenance->>'researcher_initial'
FROM experiment_specs
WHERE reproducibility->'environment_capture'->>'completeness' = 'absent';

-- preregistration 있는 실험들
SELECT identity->>'short_id', rigor->'preregistration_marker'->>'url_or_id'
FROM experiment_specs
WHERE (rigor->'preregistration_marker'->>'present')::bool = true;
```

랩 전체의 reproducibility / rigor trend 가 query 한 방으로 보입니다.
