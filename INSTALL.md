# Install — experiment-anatomy plugin

## Prerequisites

- macOS / Linux PC (Windows WSL OK)
- Python 3.11+ (only required if you want to run the PostgreSQL upserter)
- `git`, `curl`
- Claude Code CLI installed (claude.ai/code → install)

## 1. Install via marketplace

```bash
# Add this repo as a marketplace, then install the plugin:
/plugin marketplace add CSNL-vnilab/experiment-anatomy
/plugin install experiment-anatomy@experiment-anatomy-marketplace
```

Claude Code clones the repo into `~/.claude/plugins/cache/<owner>/experiment-anatomy/<version>/`,
registers the marketplace + enabled plugin in `~/.claude/settings.json`,
and the next session will surface:

- `/experiment-anatomy:analyze`
- `/experiment-anatomy:review`
- `/experiment-anatomy:export`

## 2. Apply the PostgreSQL DDL (one time per lab)

If you want to land specs into the lab's PostgreSQL `experiment_specs` +
child tables, apply the DDL block in
[`schemas/postgres-mapping.md`](./schemas/postgres-mapping.md):

```bash
psql "$DATABASE_URL" -f <(awk '/^```sql$/,/^```$/' schemas/postgres-mapping.md | sed '1d;$d')
```

(Or copy-paste the DDL by hand — it's seven `CREATE TABLE`s.)

## 3. Install Python deps for the upserter (optional)

```bash
pip install --upgrade psycopg2-binary jsonschema
```

The upserter (`scripts/upsert-to-postgres.py`) needs:

- `psycopg2-binary` — PostgreSQL client
- `jsonschema` — validates the spec against `experiment-spec.schema.json`
  before any write

## 4. Verify

In a Claude Code session in a non-empty directory:

```
/experiment-anatomy:analyze
```

If the slash command shows up and the agent starts Pass 1, the install
is good. The anatomist will print a one-line progress note before each
of 12 passes.

## Uninstall

```bash
/plugin uninstall experiment-anatomy@experiment-anatomy-marketplace
/plugin marketplace remove experiment-anatomy-marketplace
```

Or manually:

```bash
rm -rf ~/.claude/plugins/cache/<owner>/experiment-anatomy/
# edit ~/.claude/settings.json — remove the marketplace + enabledPlugins entry
```

## Troubleshooting

- **`/experiment-anatomy:analyze` not found** — `/plugin list` to confirm
  the plugin is enabled; restart Claude Code.
- **JSON output fails schema validation** — the anatomist agent should
  refuse to emit invalid JSON. If you got an invalid file, please open
  an issue with the inputs (or a redacted snippet) so the prompt can be
  hardened.
- **PostgreSQL upsert fails** — run with `DRY_RUN=1` first to see the
  SQL; check that the DDL has been applied; check `DATABASE_URL`
  credentials.
- **The model isn't actually Opus** — the `model: opus` frontmatter on
  `agents/anatomist.md` requests Opus; if your Claude Code session is
  on a different model, the slash command runs with whatever's active.
  Switch to Opus before invoking for best results (the multi-pass
  reasoning is the value).
