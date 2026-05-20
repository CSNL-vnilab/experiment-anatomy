# PostgreSQL mapping — `experiment-anatomy` output → lab DB

The plugin's JSON output (`schemas/experiment-spec.schema.json`) is designed
to land in PostgreSQL with **zero re-shaping at the consumer**: every list
in the JSON becomes one child table, and `identity.short_id` is the
upsert key.

This document is the contract between the plugin and any consumer that
ingests its output (the lab-reservation app, an admin batch importer, an
analysis dashboard).

## Tables

### `experiment_specs` — one row per analysis run

```sql
create table experiment_specs (
  id              uuid primary key default gen_random_uuid(),
  short_id        text not null,                 -- identity.short_id ; the natural key
  title           text not null,
  paradigm_genre  text not null,
  summary         text not null,
  research_question text,
  version         text,

  -- platform
  framework          text not null,
  language           text not null,
  framework_version  text,
  language_runtime   text,
  detection_confidence numeric(3,2),

  -- hierarchy roll-ups (the full session→phase tree lives in spec_phases)
  hierarchy_one_liner text not null,
  n_sessions          integer,
  total_trials_estimate integer,
  estimated_duration_min numeric,

  design_matrix_summary text,

  -- reproducibility / rigor — score + components
  reproducibility_score integer check (reproducibility_score between 0 and 100),
  rigor_score           integer check (rigor_score between 0 and 100),

  -- full JSON document for fields not flattened into columns
  raw_spec        jsonb not null,

  -- provenance
  plugin_version  text not null,
  schema_version  text not null,
  analyzed_at     timestamptz not null,
  model           text,
  source_root     text,
  researcher_initial text,

  created_at      timestamptz not null default now(),
  updated_at      timestamptz not null default now(),

  unique (short_id, version)   -- upsert key
);

create index on experiment_specs (paradigm_genre);
create index on experiment_specs (framework);
create index on experiment_specs (researcher_initial);
create index on experiment_specs using gin (raw_spec);
```

### `spec_phases` — session/phase tree

```sql
create table spec_phases (
  id            uuid primary key default gen_random_uuid(),
  spec_id       uuid not null references experiment_specs(id) on delete cascade,
  session_index integer not null,
  phase_kind    text not null,
  phase_label   text,
  day_range     text,
  n_blocks      integer,
  n_trials_per_block integer,
  applies_when  text,
  description   text,
  ord           integer not null              -- preserve declared order
);
create index on spec_phases (spec_id, session_index, ord);
```

### `spec_factors`, `spec_conditions`, `spec_parameters`, `spec_saved_variables`

One child table per JSON list. Each carries `spec_id` (FK with cascade
delete) and an `ord` integer to preserve declared order. Columns mirror
the JSON object's fields verbatim; complex sub-objects (evidence arrays,
factor_assignments map) stay as `jsonb`.

```sql
create table spec_factors (
  id      uuid primary key default gen_random_uuid(),
  spec_id uuid not null references experiment_specs(id) on delete cascade,
  ord     integer not null,

  name         text not null,
  display_name text,
  type         text not null,                 -- categorical / continuous / ordinal
  levels       jsonb not null default '[]'::jsonb,
  level_source text,
  role         text not null,
  description  text,
  evidence     jsonb not null default '[]'::jsonb
);
create index on spec_factors (spec_id, ord);
create index on spec_factors (name);
create index on spec_factors (role);

create table spec_conditions (
  id      uuid primary key default gen_random_uuid(),
  spec_id uuid not null references experiment_specs(id) on delete cascade,
  ord     integer not null,
  label   text not null,
  factor_assignments jsonb not null default '{}'::jsonb,
  description text
);
create index on spec_conditions (spec_id, ord);

create table spec_parameters (
  id      uuid primary key default gen_random_uuid(),
  spec_id uuid not null references experiment_specs(id) on delete cascade,
  ord     integer not null,
  name    text not null,
  value   jsonb,                              -- string/number/boolean/null
  type    text,
  unit    text,
  shape   text not null,
  description text,
  evidence jsonb not null default '[]'::jsonb
);
create index on spec_parameters (spec_id, ord);
create index on spec_parameters (name);

create table spec_saved_variables (
  id      uuid primary key default gen_random_uuid(),
  spec_id uuid not null references experiment_specs(id) on delete cascade,
  ord     integer not null,
  name    text not null,
  scale   text not null,                      -- per_trial / per_block / …
  category text,
  format  text not null,
  unit    text,
  sink    text,
  description text,
  evidence jsonb not null default '[]'::jsonb
);
create index on spec_saved_variables (spec_id, ord);
create index on spec_saved_variables (scale);
create index on spec_saved_variables (category);
```

### `spec_open_questions` — confirmation queue

```sql
create table spec_open_questions (
  id      uuid primary key default gen_random_uuid(),
  spec_id uuid not null references experiment_specs(id) on delete cascade,
  ord     integer not null,
  topic   text not null,
  question text not null,
  evidence text,
  options  jsonb not null default '[]'::jsonb,
  resolved boolean not null default false,
  resolved_answer text,
  resolved_at timestamptz,
  resolved_by text
);
create index on spec_open_questions (spec_id, resolved);
```

## Upsert flow

Natural key for the parent row is `(short_id, version)`:

```sql
-- pseudocode the importer follows
insert into experiment_specs (...) values (...)
  on conflict (short_id, version) do update set
    title = excluded.title,
    paradigm_genre = excluded.paradigm_genre,
    summary = excluded.summary,
    /* … all flattened columns … */
    raw_spec = excluded.raw_spec,
    analyzed_at = excluded.analyzed_at,
    updated_at = now()
  returning id;
-- then: delete from each spec_* child where spec_id = ?, and re-insert from JSON arrays.
```

A reference Python importer lives at `scripts/upsert-to-postgres.py`.
It reads the JSON output, applies the upsert above with `INSERT … ON CONFLICT`
and `DELETE … then INSERT` for children, all inside one transaction.

## Querying

- "What's still open?" → `select short_id, question from spec_open_questions
  join experiment_specs on spec_id = experiment_specs.id where not resolved`
- "All experiments missing a sample-size justification" →
  `select short_id from experiment_specs where (raw_spec #>> '{rigor,sample_size_justification,present}') = 'false'`
- "Per-trial variables across all psychophysics experiments" →
  `select e.short_id, v.name from experiment_specs e join spec_saved_variables v on v.spec_id = e.id where e.paradigm_genre = 'psychophysics' and v.scale = 'per_trial'`

## Versioning

`schema_version` lives both in the JSON and in `experiment_specs.schema_version`.
Bump on any breaking change to JSON shape. The importer should refuse rows
whose `schema_version` is newer than the schema it knows.
