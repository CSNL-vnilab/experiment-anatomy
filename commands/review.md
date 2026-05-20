---
description: Re-run the anatomist on an existing experiment-spec.json — useful after the researcher answered some open_questions and wants the spec re-derived with their answers folded in.
argument-hint: "<path-to-existing-spec.json> [SOURCE=<code-root>] [INTERVIEW=on|off]"
---

## /experiment-anatomy:review <spec.json> [knobs]

Takes a previously emitted spec and re-derives it against the SAME
source tree, seeding the agent with prior answers so the interview only
asks what's still open.

### Arguments

- `<spec.json>` — path to an existing `experiment-spec.json` (the file
  the `/analyze` command wrote).
- `SOURCE=<path>` — override the source root. Defaults to
  `provenance.source_root` from the file.
- `INTERVIEW=on` (default) / `off`.

### Behavior

1. Load the prior spec; pull `identity`, `platform`, `provenance.source_root`,
   and any field whose researcher-supplied evidence array is non-empty.
2. Hand off to the `anatomist` agent with a seed message: "Re-derive
   this spec from the source. Prior researcher-confirmed values are
   marked with `evidence: ['interview: …']` and MUST be preserved
   verbatim unless the source no longer supports them."
3. Run only the passes whose section had `open_questions` in the prior
   spec, plus Pass 11 (rigor) and Pass 10 (reproducibility) which
   depend on the rest.
4. Emit the new spec to the same paths (or `*.review.json` if you'd
   rather not overwrite — set `OUT=<path>`).

### Use case

Researcher answers 3 of 7 open questions in chat → re-run review →
the answered 3 land in their respective fields with
`evidence: ['interview: ...']`, the remaining 4 stay queued.
