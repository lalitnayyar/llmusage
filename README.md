# LLM Usage Tracker

A Python command-line application that fetches token usage, costs, and credit balances from multiple LLM providers, stores every snapshot locally in a single SQLite database, and displays filtered reports — all from an interactive text menu. No web server, no cloud sync: your API keys and usage history stay on your machine.

---

## Overview

LLM Usage Tracker answers three questions in one place:

1. **How much am I using?** — input/output tokens and cost (where the provider API exposes them).
2. **What is my balance?** — remaining credits or prepaid balance (where available).
3. **How has usage changed over time?** — each fetch appends a timestamped row so you can compare snapshots in reports.

You configure providers once (name, label, API URL, API key), fetch on demand or for all providers at once, then review history with date and provider filters.

---

## Features

| Feature | Details |
|---|---|
| **Multi-provider support** | OpenAI, Anthropic (Claude), Google Gemini, OpenRouter, DeepSeek |
| **Single-provider fetch** | Pick one configured account from a numbered list |
| **Bulk fetch** | Refresh all configured providers in one run; failures are reported per provider |
| **Local SQLite storage** | Single file at `data/llmusage.db` — portable, easy to back up |
| **Historical snapshots** | Every fetch inserts a new row with UTC timestamp; nothing is overwritten |
| **Usage reports** | Rich terminal tables with filters by date range and provider; totals row |
| **Provider admin (CRUD)** | List, add, edit, delete providers; masked API keys in list views |
| **Session logging** | Optional per-session log files under `logs/`; state persists in the database |
| **Provider adapters** | Pluggable `BaseProvider` pattern — add new backends in `providers/` |
| **Raw API responses** | Full JSON stored in `usage_records.raw_response` for debugging |

---

## Functionality

### How a fetch works

```
Main menu → Fetch (single or all)
  → Load provider row from SQLite (id, name, api_key, api_url)
  → providers.get_adapter(name, key, url)
  → adapter.fetch_usage()  →  HTTP call to provider API
  → INSERT into usage_records (tokens, cost, balance, raw JSON, fetched_at)
  → Print summary line; optional log entry
```

Each successful fetch **adds** a record. Running fetch twice gives two rows — useful for tracking balance or usage over time.

### What gets stored per fetch

| Field | Description |
|---|---|
| `fetched_at` | UTC ISO timestamp (`YYYY-MM-DDTHH:MM:SSZ`) |
| `tokens_in` / `tokens_out` | Token counts when the API provides them |
| `cost_usd` | Cost in US dollars when available or estimated |
| `balance_usd` | Remaining balance/credits when the API exposes it |
| `raw_response` | Full JSON from the provider for troubleshooting |

### Provider configuration

Each provider row stores:

- **name** — adapter key (e.g. `openai`, `anthropic`); must match a registered adapter
- **display_label** — friendly label shown in menus (e.g. `Work OpenAI`)
- **api_url** — optional base URL override
- **api_key** — secret used for API calls (masked as `sk-ab****cdef` in list views)

Provider **names are unique** in the database (one row per name).

### Logging

When logging is **ON**:

- A new file is created at startup: `logs/usageapp-YYYYMMDD-HHMMSS.log`
- Menu actions, fetches, admin changes, and reports write timestamped lines
- The on/off setting is stored in the `config` table and survives restarts

When logging is **OFF**, errors still print to the terminal; no log file is written.

---

## Requirements

- Python 3.9 or higher (developed on 3.12)
- Dependencies: `requests`, `rich`, `python-dotenv` (see `requirements.txt`)

---

## Installation

Many Linux distributions ship Python with [PEP 668](https://peps.python.org/pep-0668/) protection, so `pip install` against the system interpreter is blocked. Use a virtual environment in the project directory.

On Debian or Ubuntu, if `python3 -m venv` fails with *ensurepip is not available*, install the venv module first (match your `python3 --version`, e.g. `python3.12-venv`):

```bash
sudo apt install python3-venv
```

Then:

```bash
cd llmusage

python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
```

Quick smoke-test (no network):

```bash
python3 -c "import sys; sys.path.insert(0,'.'); import db; db.init_db(); print('OK')"
```

---

## Running the App

```bash
.venv/bin/python llmusage.py
```

If your system allows installing packages globally, `python3 llmusage.py` works too.

On first run, `data/llmusage.db` is created automatically.

---

## User Guide

### Quick start (first-time setup)

1. **Run the app** — `.venv/bin/python llmusage.py`
2. **Add a provider** — main menu **4** → Admin **2** (Add provider)
3. **Fetch usage** — main menu **1** (one provider) or **2** (all)
4. **View report** — main menu **3** → pick a date filter
5. **Optional** — main menu **5** to enable session logging for troubleshooting

### Main menu

| # | Action | Description |
|---|---|---|
| 1 | Fetch usage — select provider | Numbered list of configured providers; fetch one |
| 2 | Fetch usage — all providers | Sequential fetch for every provider; summary of OK/failed |
| 3 | View usage report | Filtered table of stored records with totals |
| 4 | Manage providers (Admin) | CRUD submenu for provider accounts |
| 5 | Toggle logging | Turn session log file on or off (persisted) |
| 6 | Exit | Close log file and quit |

Example screen:

```
LLM Usage Tracker   logging: OFF
────────────────────────────────────────
  1. Fetch usage — select provider
  2. Fetch usage — all providers
  3. View usage report
  4. Manage providers (Admin)
  5. Toggle logging  [logging: OFF]
  6. Exit
```

### Adding a provider (Admin → Add)

From the main menu, choose **4**, then **2**.

| Field | Required | Example |
|---|---|---|
| Name | Yes | `openrouter` |
| Display label | No | `My OpenRouter Account` |
| API URL | No | `https://openrouter.ai` (blank = adapter default) |
| API Key | Yes (for real fetches) | `sk-or-v1-...` |

**Registered adapter names:** `openai`, `anthropic`, `gemini`, `openrouter`, `deepseek`

The admin UI also lists `other` as a hint, but only registered names can fetch — use an exact adapter name.

### Provider Admin submenu

| # | Action |
|---|---|
| 1 | List all providers (ID, name, label, URL, masked key, updated time) |
| 2 | Add provider |
| 3 | Edit provider (list, enter ID, press Enter to keep each field) |
| 4 | Delete provider (confirmation required) |
| 5 | Back to main menu |

### Fetching usage

**Single provider (menu 1)**

1. A table shows configured providers by number.
2. Enter the number (`0` to cancel).
3. The app calls the provider API and prints:

   ```
   Fetching openrouter...  OK  in=0  out=0  cost=$1.234500  balance=$45.6700
   ```

**All providers (menu 2)**

- Fetches each provider in order.
- Failed providers show `FAILED` with the error message; others continue.
- Ends with: `Done — N succeeded, M failed` (if any failures).

### Usage reports (menu 3)

| # | Filter |
|---|---|
| 1 | All records — last 30 days |
| 2 | One provider — enter provider ID, last 30 days |
| 3 | Today only |
| 4 | Custom — enter last **N** days |
| 5 | All time |

Report columns: **Fetched At**, **Provider**, **Tokens In**, **Tokens Out**, **Cost (USD)**, **Balance (USD)**, plus a **TOTAL** row for tokens and cost.

If no rows match the filter, you see `No records found.` — run a fetch first.

### Session logging (menu 5)

- Confirm with `y` to toggle.
- **ON:** new log at `logs/usageapp-<timestamp>.log`; path shown on screen.
- **OFF:** current log file is closed; no further writes until re-enabled.
- If logging was left ON from a previous session, a log file opens automatically at startup.

Log lines look like:

```
[2026-05-15T08:31:07Z] fetch.success | provider=openai | tokens_in=1200 tokens_out=800 cost=0.05 balance=42.0
```

### Keyboard interrupt

Press `Ctrl+C` to exit cleanly; the app closes the log file and prints goodbye.

---

## Provider Notes

What each adapter returns depends on the provider’s public API.

| Provider | Tokens | Cost | Balance | Notes |
|---|---|---|---|---|
| **OpenAI** | Monthly completion usage | From usage/billing endpoints | Credit limit when available | API URL: `https://api.openai.com` only (scheme + host). Do not paste full docs paths. Organization usage may need an [Admin API key](https://platform.openai.com/settings/organization/admin-keys) if legacy billing returns 404. |
| **Anthropic** | Monthly input/output totals | Estimated from token counts (Sonnet-style rates) | Not available via API | Uses `x-api-key` and Anthropic version header. |
| **OpenRouter** | Not on key-info endpoint | Total spend | Remaining credits | Key info endpoint for spend/balance. |
| **DeepSeek** | Not on balance endpoint | — | Remaining USD balance | Balance-focused fetch. |
| **Gemini** | — | — | — | Validates API key; [Google AI Studio](https://aistudio.google.com/usage) has no usage REST endpoint in this app. |

---

## Data Storage

All data lives in **`data/llmusage.db`** (SQLite).

| Table | Purpose |
|---|---|
| `providers` | Configured LLM accounts (unique `name`) |
| `usage_records` | One row per fetch; `ON DELETE CASCADE` when provider removed |
| `config` | App settings (`logging` = `on` / `off`) |

**Reset:** delete `data/llmusage.db` and run the app again.

**Backup:** copy `data/llmusage.db` (and optionally `logs/`).

---

## Project Structure

```
llmusage/
├── llmusage.py          # Entry point and main menu
├── db.py                # SQLite schema and queries
├── config.py            # Logging on/off wrapper
├── logger.py            # Session log file management
├── providers/
│   ├── base.py          # BaseProvider + UsageResult
│   ├── openai.py
│   ├── anthropic.py
│   ├── gemini.py
│   ├── openrouter.py
│   └── deepseek.py
├── commands/
│   ├── admin.py         # Provider CRUD
│   ├── fetch.py         # Single / all fetch
│   └── report.py        # Filtered reports
├── data/                # llmusage.db (auto-created)
├── logs/                # Session logs when logging is ON
├── requirements.txt
└── planning/            # Original requirements notes
```

---

## Adding a New Provider

1. Create `providers/<name>.py` implementing `fetch_usage() -> UsageResult`
2. Register the class in `providers/__init__.py` `REGISTRY`
3. Add the name to `KNOWN_PROVIDERS` in `commands/admin.py`

---

## Troubleshooting

| Issue | What to try |
|---|---|
| `No providers configured` | Admin → Add provider before fetching |
| `No adapter registered for provider` | Use an exact registry name (`openai`, not `OpenAI`) |
| `FAILED` on fetch | Check API key, URL, and network; enable logging and inspect `logs/` |
| OpenAI 404 / auth errors | Use base URL `https://api.openai.com`; try an organization Admin API key |
| Empty report | Run fetch first; widen date filter (e.g. option 5 — all time) |
| `UNIQUE constraint` on add | Provider name already exists — edit or delete the existing row |
| venv / pip errors on Linux | `sudo apt install python3-venv` then recreate `.venv` |

Inspect raw API payloads in the database:

```bash
sqlite3 data/llmusage.db "SELECT fetched_at, provider_id, substr(raw_response,1,200) FROM usage_records ORDER BY id DESC LIMIT 5;"
```

---

## License

See repository for license information if applicable.
