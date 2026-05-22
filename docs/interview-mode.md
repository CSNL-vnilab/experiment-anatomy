# 인터뷰 모드 — Pass 12 가 어떻게 작동하는지

`experiment-anatomy` 의 핵심 디자인 결정: **코드만으로 못 정한 것이 있으면 추측하지 않고 묻는다.** 다른 자동 도구와 가장 다른 점입니다.

## 언제 시작되나

Pass 1–11 이 끝나면 spec 안에는 채워지지 않은 필드들과 `open_questions[]` 가 쌓여 있습니다. Pass 12 는 그중 **답이 들어오면 위 필드가 material 하게 바뀌는** 질문들만 골라 물어봅니다.

```
✦ Pass 12 — 확인 인터뷰 (질문 4개 / 총 12개 후보 중 material 4개)
```

## 인터뷰 한 사이클

```
Q1 (factors):
  par.exclude.rt_min = 0.2 (analyze.m:34) — 이 값이 무엇인가요?
  ① 분석 단계 제외 기준 (RT cutoff)
  ② 실험 진행 중 제외 기준 (online 제외)
  ③ 둘 다 (분석에서도, online 에서도 사용)
  ④ 건너뜀 / 모름

>
```

- **한 번에 한 질문씩.** 동시에 두 가지를 묻지 않음.
- **한국어.** CSNL 디폴트.
- **multiple choice over open-ended.** 답이 spec field 에 매핑되려면 enum 이 편함.
- **언제나 "건너뜀 / 모름" 옵션 제공.** 모르는 게 죄가 아님.
- **항상 evidence 함께.** `(analyze.m:34)` 같은 코드 라인 — 어디서 왔는지 보여주면서 묻기.

답이 들어오면 즉시 spec 에 반영:

```
> 1
✦ 반영: rigor.exclusion_rules.rules_found 에 "RT < 200 ms 제외 (분석 단계)" 추가, evidence: analyze.m:34
✦ open_questions 에서 q-d4a7 제거

Q2 (parameters):
  par.feedback_duration_ms 가 docs/protocol.md:24 에는 있는데 코드 어디에도 안 보입니다. 어디서 설정되나요?
  ① main_duration.m 의 어딘가 (제가 못 찾은 거)
  ② 별도 config 파일 (어디인지 알려주세요)
  ③ README 가 잘못 쓰여진 것 (실제로는 사용 안 함)
  ④ 건너뜀 / 모름
>
```

## 언제 끝나나

세 가지 조건 중 하나:

1. **모든 material question 이 풀렸을 때** — 다음 unresolved 질문이 spec 의 어느 필드도 material 하게 바꾸지 않으면 (e.g. "monitor 해상도가 1920×1080 인가 1440×900 인가" 는 보통 의미가 없음) 자동 종료.
2. **"skip / 그만 / later / 나중에" / "건너뜀" 라고 답하면** — 그 질문은 `open_questions[]` 에 남고 인터뷰 종료. 나머지도 자동으로 모두 그 list 에 들어감.
3. **10개 질문 정중함 cap.** 이걸 넘는 일은 거의 없음 — 보통 4–6개.

종료되면 spec 이 emit:

```
✦ Pass 12 종료 (3 questions answered, 1 skipped)
✦ experiment-spec.json 작성 중...
✦ experiment-spec-summary.md 작성 중...
```

## 연구자가 push back 했을 때

가장 흔하고 가장 중요한 경우. anatomist 가 잘못 추출했을 때:

```
> 그건 IV 아니야. par.tp.iti 는 그냥 ITI 길이고, condition 마다 다르지 않음.
```

이 답이 들어오면:

```
✦ factors[] 에서 "tp_iti" entry 제거
✦ parameters[] 에 "par.tp.iti" 추가 (shape=constant, value=0.5)
✦ evidence: "interview: researcher confirmed not an IV"
```

**연구자가 verdict. 에이전트는 harness.** 추출이 틀렸다고 말하면 즉시 spec 에서 빼고, evidence 에 그 인터뷰 라인을 박아둡니다. 다음 / 비슷한 경우에 같은 실수 반복하지 않도록.

## 인터뷰를 건너뛰고 싶을 때

```
/experiment-anatomy:analyze /path/ INTERVIEW=off
```

이러면 Pass 12 가 안 돌고, 모든 unresolved 가 `open_questions[]` 로 출력됩니다. 나중에:

```
/experiment-anatomy:review experiment-spec.json
```

으로 다시 들어가 답하면 spec 이 갱신됩니다.

## 자동화된 batch 분석

여러 실험을 한꺼번에 분석할 때는 `INTERVIEW=off` 를 디폴트로 쓰고, 출력된 `open_questions[]` 들을 PostgreSQL `spec_open_questions` 테이블에 적재 → 웹 UI 에서 모아 답하는 흐름을 권장.

```bash
for exp in TimeExp1 TimeExp2 RingExp; do
  /experiment-anatomy:analyze /Volumes/.../$exp INTERVIEW=off RESEARCHER_INIT=JOP
  /experiment-anatomy:export ./experiment-spec.json
done

psql "$DATABASE_URL" -c "SELECT short_id, topic, question FROM spec_open_questions WHERE answered_at IS NULL ORDER BY short_id, topic;"
```

## 인터뷰 답변의 evidence 표기

답변이 spec 의 필드를 채우면, 그 필드의 `evidence` 배열은:

```json
"evidence": ["interview: q-d4a7"]
```

`q-d4a7` 는 short hash. 같은 답이 여러 필드에 영향을 주면 같은 hash 가 여러 곳에 박힘 — provenance 추적용.

연구자가 "interview: confirmed" 같은 free-form note 을 남겼다면 그것이 그대로 들어갑니다.

## 무엇을 절대 묻지 않는가

- **이미 코드에 literal 로 있는 것** (`nTrials = 40` 이 보이는데 trial 수 묻지 않음).
- **이미 docs 에 명시된 것** (README 가 `paradigm: estimation` 이라고 쓰면 paradigm_genre 묻지 않음).
- **spec field 를 material 하게 바꾸지 않는 cosmetic detail** (모니터 모델, 의자 높이 등).
- **연구자 개인 정보** (참가자 이름, IRB 번호 같은 것 — code 에 우연히 노출되어도 spec 에 안 옮김).

## 인터뷰가 안 보이고 바로 끝나는 경우

세 가지 가능성:

1. **모든 정보가 코드에 있음** — 가장 깨끗한 케이스. 축하합니다.
2. **`INTERVIEW=off` 가 켜져 있음** — 명시적으로 끔.
3. **Anatomist 가 "추측해서 채워버림"** — bug. 이런 경우 `open_questions[]` 에 등록됐어야 할 항목이 silently 채워졌을 가능성. 출력 JSON 의 `evidence` 가 모두 `file:line` 또는 `interview:` prefix 가 있는지 확인. 없는 게 있으면 issue.

## 인터뷰가 너무 길다고 느껴질 때

`INTERVIEW=off` 로 batch 모드. 또는 Pass 11 까지 끝낸 후 인터뷰가 시작되면 첫 질문에 `skip` 답해서 모두 `open_questions[]` 로 보내고 나중에 한 번에 처리.

너무 많이 물으면 (>6개) — anatomist 가 evidence 를 충분히 못 모았다는 signal. `MAX_BYTES` 를 키우거나 (`MAX_BYTES=1500000`), `DOCS=docs/protocol.md,docs/methods.md` 로 명시적 docs 경로 전달.

## 인터뷰 답변을 나중에 수정하고 싶을 때

세 가지 방법:

1. **JSON 직접 편집** + schema 재검증:
   ```bash
   $EDITOR experiment-spec.json
   python3 -c "import json, jsonschema; jsonschema.validate(json.load(open('experiment-spec.json')), json.load(open('schemas/experiment-spec.schema.json')))"
   ```

2. **`/experiment-anatomy:review`** — 기존 spec 을 입력으로 다시 들어가 변경된 부분만 다시 묻기.

3. **DB 에 이미 적재된 후 수정**: PostgreSQL `experiment_specs` row 를 UPDATE — `/experiment-anatomy:export` 는 idempotent 라 재실행하면 덮어쓰기.

## 인터뷰 디자인 철학

다른 자동 도구는 보통 "최선 추측 + 사용자가 다 검토" 인터페이스. 이 플러그인은 **"추측 안 하고 modular 한 질문 몇 개"** 를 선택. 이유:

- 추측은 종종 그럴듯해서 사용자가 검토 안 함 → silent 오류.
- 명시적 질문은 시간이 들지만 — 정확함. 한 번 답하면 영구.
- "건너뜀" 도 정보 — `open_questions[]` 에 남아 나중에 답할 기회.
- 인터뷰 답변은 evidence trail 의 일부 — DB 에 함께 적재.

`csnl-archive` 플러그인 (자매 플러그인) 도 같은 grounded-interview 패턴을 *project* 레벨에서 씁니다. 이 디자인이 노벨한 게 아니라 — 검증된 패턴을 experiment 레벨에 적용한 것.

## 한국어 외 다른 언어로 인터뷰

`agents/anatomist.md` 의 Hard rule 5: **"Korean prose, English keys"**. JSON keys/enums 는 영어 (schema 가 enforce), 자유 텍스트 (summary, description, notes, interview question) 는 연구자가 쓰는 언어 — CSNL 디폴트는 한국어. 영어로 답해도 받아들이고, 영어 prose 가 자연스러우면 영어로 question 을 생성합니다.

다른 lab fork 시 system prompt 의 한국어 part 를 자기 언어로 바꾸면 됩니다.
