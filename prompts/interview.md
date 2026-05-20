# Interview protocol — map-first grounded, one Q at a time

Mirrors the lab archiver agent's methodology, applied to experiment
deconstruction.

## Core rules

1. **One concern per question.** Don't combine "What's the role of X
   AND what are its levels?" — ask role first, levels next.
2. **Grounded.** Every question cites the code evidence that prompts
   it. The researcher sees the file:line and decides.
3. **Multi-choice over open-ended.** Offer 2–6 concrete options; "기타"
   / "다른 값 직접 입력" is the last option only when needed.
4. **Always offer "건너뜀 / 모름".** Never trap the researcher in a
   forced choice.
5. **Past-focused.** Ask about what the code DOES, not what they MIGHT
   want it to do. "이 변수는 trial 마다 바뀌나요?" — not "이 변수를
   IV 로 쓰시겠습니까?"
6. **Politeness cap.** ≤10 questions per `/analyze` run. After 10,
   ship remaining open_questions and stop.

## When to ask vs. when to ship as open_question

ASK in the live interview (Pass 12) when:
- The answer materially changes a flattened column in the spec.
- The code has clear evidence to anchor a multiple-choice question.
- The researcher's response is fast (single token / multi-choice).

SHIP AS OPEN QUESTION (no live ask) when:
- The answer requires looking up an external file (CSV, paper, OSF link).
- The interview cap (10) has been reached.
- `INTERVIEW=off` was passed.
- The ambiguity is about the experiment design intent, not the code.

## Question template

```
질문 N/총M  ·  [topic]
근거: <file:line> (또는 "코드 전반 — 명시적 마커 없음")
질문: <one concrete question>
선택지:
  1. <option 1 with concrete value/role/whatever>
  2. <option 2>
  3. <option 3>
  4. 건너뜀 — open_question 으로 큐에 남기기
  5. 모름 — 그대로 둠
```

The researcher answers with the number (or types text — both fine).

## Folding the answer back

When the researcher gives an answer:

1. Update the corresponding field in the spec.
2. Add an evidence entry: `"interview: <q-hash 8 chars>"`. (The
   slash-command's orchestration writes the actual log to
   `~/.claude/experiment-anatomy/interview.jsonl` so the hash maps
   to the literal Q/A.)
3. Remove the matching item from `open_questions[]`.
4. Announce "반영됨 — 다음 질문 N+1" and continue.

If the answer contradicts a different field elsewhere, ALWAYS prefer
the researcher's answer — they own the experiment. Edit the other field
silently and note in `summary` if it was material.

## Stop conditions

- All material questions resolved. Print a single sentence "확인할 항목
  없음 — 결과 emit 합니다" and proceed to output.
- Researcher types `skip`, `그만`, `later`, `나중에` — accept,
  ship remaining open_questions.
- 10 questions asked — same.

## Example session (PsychoPy)

```
질문 1/3  ·  factors
근거: psychopy_estimation/estimation.py:42 — `data.importConditions('cond.csv')`
질문: 'cond.csv' 가 정의하는 *조작변수* 의 이름들이 코드에서 보이는
  thisTrial['stim_duration'] / thisTrial['fixation_duration'] 두 개로 맞나요?
선택지:
  1. 맞음 — 이 둘이 전부
  2. 한 개 더 있음 — 직접 입력하겠음
  3. csv 파일이 없어서 잘 모름
  4. 건너뜀
```

Researcher answers "1" → set factors=[stim_duration, fixation_duration],
levels=[] for both (CSV-sourced), level_source='conditions-file'.
Evidence: 'interview: a1b2c3d4'.

## Hash format

q-hash = first 8 chars of sha256(question + topic + ISO timestamp).
Used purely as a back-reference into `interview.jsonl`.
