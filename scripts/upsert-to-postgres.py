#!/usr/bin/env python3
"""
upsert-to-postgres.py — land an experiment-spec.json into the lab's
PostgreSQL `experiment_specs` (+ child) tables, transactionally.

Usage:
    python3 upsert-to-postgres.py path/to/experiment-spec.json \
        [--database-url postgresql://...] [--dry-run]

Behavior:
    1. Validate JSON against schemas/experiment-spec.schema.json.
    2. Refuse if schema_version is newer than this script knows.
    3. BEGIN.
    4. INSERT … ON CONFLICT (short_id, version) DO UPDATE on
       experiment_specs → spec_id.
    5. DELETE existing children for spec_id, re-INSERT from JSON,
       preserving declared `ord`.
    6. COMMIT (or ROLLBACK on any error).

Reads connection from --database-url first, then $DATABASE_URL,
then a sibling .env (DATABASE_URL=postgresql://…).

Requires: psycopg2-binary, jsonschema.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# This script's known schema. Bump when schemas/experiment-spec.schema.json
# breaks a column. A spec with a newer schema_version is rejected so a
# stale upserter can't lossily import a richer document.
KNOWN_SCHEMA_VERSION = "1.0.0"

SCHEMA_FILE = (
    Path(__file__).resolve().parent.parent
    / "schemas"
    / "experiment-spec.schema.json"
)


def die(msg: str, code: int = 1) -> "None":
    print(f"upsert-to-postgres: ERROR: {msg}", file=sys.stderr)
    sys.exit(code)


def load_database_url(arg_url: str | None) -> str:
    if arg_url:
        return arg_url
    env_url = os.environ.get("DATABASE_URL")
    if env_url:
        return env_url
    # fall back to a sibling .env in the plugin dir
    plugin_env = Path(__file__).resolve().parent.parent / ".env"
    if plugin_env.exists():
        for line in plugin_env.read_text().splitlines():
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, _, v = line.partition("=")
            if k.strip() == "DATABASE_URL":
                return v.strip().strip('"').strip("'")
    die(
        "no DATABASE_URL — pass --database-url, set $DATABASE_URL, or put it in <plugin-dir>/.env"
    )
    return ""  # unreachable; satisfy type checker


def load_spec(path: Path) -> dict[str, Any]:
    try:
        spec = json.loads(path.read_text(encoding="utf-8"))
    except Exception as e:
        die(f"could not read/parse {path}: {e}")
        raise  # unreachable

    sv = spec.get("schema_version")
    if sv != KNOWN_SCHEMA_VERSION:
        die(
            f"schema_version mismatch: spec has {sv!r}, this script knows {KNOWN_SCHEMA_VERSION!r}. "
            "Upgrade the upserter or downgrade the spec."
        )

    try:
        import jsonschema  # type: ignore
    except ImportError:
        print(
            "upsert-to-postgres: jsonschema not installed — skipping JSON-schema validation. "
            "Install with `pip install jsonschema` for stricter ingest.",
            file=sys.stderr,
        )
    else:
        schema = json.loads(SCHEMA_FILE.read_text())
        try:
            jsonschema.validate(spec, schema)
        except jsonschema.ValidationError as e:
            die(f"spec failed schema validation: {e.message} (path: {list(e.absolute_path)})")
    return spec


# ---------------------------------------------------------------------------
# SQL generators (parent + 6 children). Each returns (sql, params_seq).
# ---------------------------------------------------------------------------
def parent_upsert(spec: dict[str, Any]) -> tuple[str, list[Any]]:
    ident = spec["identity"]
    plat = spec["platform"]
    hier = spec["hierarchy"]
    repro = spec["reproducibility"]["score"]["overall"]
    rigor = spec["rigor"]["score"]["overall"]
    prov = spec["provenance"]
    sql = """
    insert into experiment_specs (
      short_id, title, paradigm_genre, summary, research_question, version,
      framework, language, framework_version, language_runtime, detection_confidence,
      hierarchy_one_liner, n_sessions, total_trials_estimate, estimated_duration_min,
      design_matrix_summary,
      reproducibility_score, rigor_score,
      raw_spec,
      plugin_version, schema_version, analyzed_at, model, source_root, researcher_initial,
      created_at, updated_at
    )
    values (
      %s, %s, %s, %s, %s, %s,
      %s, %s, %s, %s, %s,
      %s, %s, %s, %s,
      %s,
      %s, %s,
      %s::jsonb,
      %s, %s, %s, %s, %s, %s,
      now(), now()
    )
    on conflict (short_id, version) do update set
      title = excluded.title,
      paradigm_genre = excluded.paradigm_genre,
      summary = excluded.summary,
      research_question = excluded.research_question,
      framework = excluded.framework,
      language = excluded.language,
      framework_version = excluded.framework_version,
      language_runtime = excluded.language_runtime,
      detection_confidence = excluded.detection_confidence,
      hierarchy_one_liner = excluded.hierarchy_one_liner,
      n_sessions = excluded.n_sessions,
      total_trials_estimate = excluded.total_trials_estimate,
      estimated_duration_min = excluded.estimated_duration_min,
      design_matrix_summary = excluded.design_matrix_summary,
      reproducibility_score = excluded.reproducibility_score,
      rigor_score = excluded.rigor_score,
      raw_spec = excluded.raw_spec,
      plugin_version = excluded.plugin_version,
      schema_version = excluded.schema_version,
      analyzed_at = excluded.analyzed_at,
      model = excluded.model,
      source_root = excluded.source_root,
      researcher_initial = excluded.researcher_initial,
      updated_at = now()
    returning id;
    """
    params = [
        ident.get("short_id"),
        ident["title"],
        ident["paradigm_genre"],
        ident["summary"],
        ident.get("research_question"),
        ident.get("version"),
        plat["framework"],
        plat["language"],
        plat.get("framework_version"),
        plat.get("language_runtime"),
        plat.get("detection_confidence"),
        hier["one_liner"],
        hier.get("n_sessions"),
        hier.get("total_trials_estimate"),
        hier.get("estimated_duration_min"),
        spec.get("design_matrix_summary"),
        repro,
        rigor,
        json.dumps(spec, ensure_ascii=False),
        prov["plugin_version"],
        prov["schema_version"],
        prov["analyzed_at"],
        prov.get("model"),
        prov.get("source_root"),
        prov.get("researcher_initial"),
    ]
    return sql, params


def child_inserts(spec_id: str, spec: dict[str, Any]) -> list[tuple[str, list[Any]]]:
    out: list[tuple[str, list[Any]]] = []

    # delete-then-reinsert for each list (preserves declared order via `ord`)
    delete_targets = [
        "spec_phases",
        "spec_factors",
        "spec_conditions",
        "spec_parameters",
        "spec_saved_variables",
    ]
    for t in delete_targets:
        out.append((f"delete from {t} where spec_id = %s", [spec_id]))
    # open_questions: keep resolved rows; replace open ones
    out.append(
        (
            "delete from spec_open_questions where spec_id = %s and not resolved",
            [spec_id],
        )
    )

    # phases (session × phase tree)
    ord_i = 0
    for sess in spec["hierarchy"].get("sessions", []):
        for phase in sess.get("phases", []):
            ord_i += 1
            out.append(
                (
                    """
                insert into spec_phases (spec_id, session_index, phase_kind, phase_label,
                  day_range, n_blocks, n_trials_per_block, applies_when, description, ord)
                values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                    [
                        spec_id,
                        sess["index"],
                        phase["kind"],
                        phase.get("label"),
                        sess.get("day_range"),
                        phase.get("n_blocks"),
                        phase.get("n_trials_per_block"),
                        phase.get("applies_when"),
                        phase.get("description"),
                        ord_i,
                    ],
                )
            )

    # factors
    for i, f in enumerate(spec.get("factors", [])):
        out.append(
            (
                """
            insert into spec_factors (spec_id, ord, name, display_name, type, levels,
              level_source, role, description, evidence)
            values (%s, %s, %s, %s, %s, %s::jsonb, %s, %s, %s, %s::jsonb)
            """,
                [
                    spec_id,
                    i,
                    f["name"],
                    f.get("display_name"),
                    f["type"],
                    json.dumps(f.get("levels", []), ensure_ascii=False),
                    f.get("level_source"),
                    f["role"],
                    f.get("description"),
                    json.dumps(f.get("evidence", []), ensure_ascii=False),
                ],
            )
        )

    # conditions
    for i, c in enumerate(spec.get("conditions", [])):
        out.append(
            (
                """
            insert into spec_conditions (spec_id, ord, label, factor_assignments, description)
            values (%s, %s, %s, %s::jsonb, %s)
            """,
                [
                    spec_id,
                    i,
                    c["label"],
                    json.dumps(c.get("factor_assignments", {}), ensure_ascii=False),
                    c.get("description"),
                ],
            )
        )

    # parameters
    for i, p in enumerate(spec.get("parameters", [])):
        # value can be string|number|boolean|null — wrap to jsonb so PostgreSQL
        # can store the literal without a type column branch.
        val = p.get("value")
        out.append(
            (
                """
            insert into spec_parameters (spec_id, ord, name, value, type, unit, shape,
              description, evidence)
            values (%s, %s, %s, %s::jsonb, %s, %s, %s, %s, %s::jsonb)
            """,
                [
                    spec_id,
                    i,
                    p["name"],
                    json.dumps(val, ensure_ascii=False),
                    p.get("type"),
                    p.get("unit"),
                    p["shape"],
                    p.get("description"),
                    json.dumps(p.get("evidence", []), ensure_ascii=False),
                ],
            )
        )

    # saved variables
    for i, s in enumerate(spec.get("saved_variables", [])):
        out.append(
            (
                """
            insert into spec_saved_variables (spec_id, ord, name, scale, category, format,
              unit, sink, description, evidence)
            values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb)
            """,
                [
                    spec_id,
                    i,
                    s["name"],
                    s["scale"],
                    s.get("category"),
                    s["format"],
                    s.get("unit"),
                    s.get("sink"),
                    s.get("description"),
                    json.dumps(s.get("evidence", []), ensure_ascii=False),
                ],
            )
        )

    # open questions (only the un-resolved ones; resolved rows persist)
    for i, q in enumerate(spec.get("open_questions", [])):
        out.append(
            (
                """
            insert into spec_open_questions (spec_id, ord, topic, question, evidence, options)
            values (%s, %s, %s, %s, %s, %s::jsonb)
            """,
                [
                    spec_id,
                    i,
                    q["topic"],
                    q["question"],
                    q.get("evidence"),
                    json.dumps(q.get("options", []), ensure_ascii=False),
                ],
            )
        )

    return out


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("spec_file", type=Path)
    p.add_argument("--database-url", default=None)
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="Print the SQL that would run (without parameter substitution) and exit.",
    )
    args = p.parse_args()

    if not args.spec_file.exists():
        die(f"no such file: {args.spec_file}")

    spec = load_spec(args.spec_file)
    db_url = load_database_url(args.database_url)

    parent_sql, parent_params = parent_upsert(spec)
    print(
        f"[upsert] {spec['identity'].get('short_id') or spec['identity']['title']} "
        f"v{spec['identity'].get('version') or '-'} "
        f"({spec['platform']['framework']}/{spec['platform']['language']}) "
        f"→ {len(spec.get('factors',[]))} factors, "
        f"{len(spec.get('parameters',[]))} params, "
        f"{len(spec.get('saved_variables',[]))} saved, "
        f"{len(spec.get('open_questions',[]))} open Qs"
    )

    if args.dry_run:
        print("\n-- experiment_specs upsert --")
        print(parent_sql.strip())
        # we don't have spec_id yet in dry-run; substitute a placeholder
        for sql, _ in child_inserts("<spec_id>", spec):
            print(f"\n-- child --\n{sql.strip()}")
        print("\n[dry-run] no DB connection opened. Use without --dry-run to commit.")
        return 0

    try:
        import psycopg2  # type: ignore
    except ImportError:
        die("psycopg2-binary not installed — `pip install psycopg2-binary`")
        return 1

    conn = psycopg2.connect(db_url)  # type: ignore[name-defined]
    try:
        with conn:
            with conn.cursor() as cur:
                cur.execute(parent_sql, parent_params)
                row = cur.fetchone()
                if row is None:
                    raise RuntimeError("parent upsert did not return an id")
                spec_id = row[0]
                for sql, params in child_inserts(spec_id, spec):
                    cur.execute(sql, params)
                print(f"[upsert] OK — spec_id = {spec_id} (committed)")
    finally:
        conn.close()

    print(
        f"[next] {len(spec.get('open_questions', []))} open question(s) queued in "
        f"spec_open_questions; mark resolved as the researcher answers them."
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
