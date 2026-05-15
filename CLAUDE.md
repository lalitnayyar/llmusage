# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Install dependencies (venv avoids PEP 668 externally-managed-environment on Debian/Ubuntu).
# If venv creation fails: sudo apt install python3-venv  (or python3.12-venv to match your Python)
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt

# Run the application
.venv/bin/python llmusage.py

# Quick module smoke-test (no external deps needed)
python3 -c "import sys; sys.path.insert(0,'.'); import db; db.init_db(); print('OK')"
```

## Architecture

The app is a Python 3.12 CLI with a SQLite backend (`data/llmusage.db`). Entry point is `llmusage.py`, which runs an interactive menu loop.

### Module responsibilities

| Module | Role |
|---|---|
| `db.py` | All SQLite access — schema init, CRUD for `providers`, `usage_records`, `config` tables |
| `config.py` | Thin wrapper over the `config` table; exposes `logging_enabled()` / `set_logging()` |
| `logger.py` | Session-scoped log file (`logs/usageapp-<timestamp>.log`); `log(action, provider, detail)` is a no-op when logging is off |
| `providers/__init__.py` | `REGISTRY` dict + `get_adapter(name, key, url)` factory |
| `providers/base.py` | `BaseProvider` ABC + `UsageResult` dataclass — the contract every adapter must satisfy |
| `providers/<name>.py` | One adapter per provider; calls that provider's REST API and returns a `UsageResult` |
| `commands/admin.py` | Interactive provider CRUD (list / add / edit / delete) |
| `commands/fetch.py` | Single-provider and all-providers fetch flows; calls adapter, writes `usage_records` |
| `commands/report.py` | Filtered report view with per-provider totals using `rich.Table` |

### Data flow for a fetch

```
llmusage.py menu → commands/fetch.py
  → db.provider_list() / db.provider_get()
  → providers.get_adapter(name, key, url)
  → adapter.fetch_usage()   # HTTP call
  → db.record_insert(...)
  → logger.log(...)
```

### Adding a new provider

1. Create `providers/<name>.py` implementing `BaseProvider.fetch_usage() -> UsageResult`
2. Register it in `providers/__init__.py` `REGISTRY`
3. Add the name to `commands/admin.py` `KNOWN_PROVIDERS` list

### Logging behaviour

Logging state persists in the `config` table (`key='logging'`, value `'on'`/`'off'`). When enabled, a new log file is opened at startup; every `commands/` action calls `logger.log()`. Toggling off mid-session closes the current file.
