---
description: Push an experiment-spec.json into the lab's PostgreSQL experiment_specs table via the upserter script. One-shot, transactional — parent row + all spec_* children replaced together.
argument-hint: "<path-to-spec.json> [DATABASE_URL=...] [DRY_RUN=1]"
---

## /experiment-anatomy:export <spec.json> [knobs]

Run the reference Python upserter against the lab's PostgreSQL:

```bash
python3 <plugin-dir>/scripts/upsert-to-postgres.py \
    <spec.json> \
    --database-url "$DATABASE_URL"
```

### Arguments

- `<spec.json>` — output of `/experiment-anatomy:analyze`. Required.
- `DATABASE_URL=postgresql://…` — connection string. If omitted, the
  script reads `$DATABASE_URL` from env, then falls back to a `.env`
  file in the plugin dir.
- `DRY_RUN=1` — print the SQL the script would run and exit. Nothing
  is committed.

### What the script does (atomic, single transaction)

1. Validate the JSON against `schemas/experiment-spec.schema.json`.
   Refuse if `schema_version` is newer than the script knows.
2. `BEGIN`.
3. `INSERT INTO experiment_specs (…) VALUES (…)
    ON CONFLICT (short_id, version) DO UPDATE SET … RETURNING id` — get
    `spec_id`.
4. `DELETE FROM spec_phases WHERE spec_id = ?` (cascade-rebuild children).
5. Same for `spec_factors`, `spec_conditions`, `spec_parameters`,
    `spec_saved_variables`.
6. `DELETE FROM spec_open_questions WHERE spec_id = ? AND NOT resolved`
    — keep researcher-resolved rows; replace only the open ones.
7. Bulk-insert all rebuilt children, preserving `ord`.
8. `COMMIT`.

Any error → `ROLLBACK`; nothing changes in the DB.

### Tables touched

`experiment_specs`, `spec_phases`, `spec_factors`, `spec_conditions`,
`spec_parameters`, `spec_saved_variables`, `spec_open_questions`.

Schema: see `schemas/postgres-mapping.md`.

### Notes

- Requires the lab's PostgreSQL DDL to be applied first (the DDL block
  in `schemas/postgres-mapping.md`).
- The DB user needs `INSERT`, `UPDATE`, `DELETE` on the seven tables.
- Per-researcher RLS scoping is the consumer's responsibility — this
  script writes whatever it's given.
