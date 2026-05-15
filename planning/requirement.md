# LLM Usage Tracker — Requirements Document

## Overview

A Python command-line application that fetches, stores, and displays token usage, costs, and current balance from multiple LLM providers. Data is persisted locally in a SQLite database. Supports provider management, selective fetching, and optional activity logging.

---

## Functional Requirements

### 1. Provider Management (Admin)

- Add a new LLM provider with:
  - Provider name (e.g., `openai`, `gemini`, `claude`, `openrouter`, `deepseek`)
  - API base URL or command endpoint
  - API key / UID
  - Optional: display label, notes
- Edit an existing provider's details
- Delete a provider (with confirmation prompt)
- List all configured providers (table view: name, URL, masked key, last fetched)

### 2. Usage Fetch — Individual Provider

- User selects a single provider from the configured list
- App connects using that provider's stored credentials
- Fetches: input tokens used, output tokens used, estimated cost, current balance/credit remaining
- Saves fetched record to the database with a timestamp

### 3. Usage Fetch — All / Batch

- Iterates over all configured providers in sequence
- Fetches usage for each and saves to the database
- Prints a per-provider summary on completion
- Skips and logs any provider that returns an error, continuing with the rest

### 4. View / Report Usage

- Display stored usage records filtered by:
  - Provider
  - Date range (today / last N days / custom range)
- Aggregate totals: total tokens in, total tokens out, total cost per provider
- Output as a formatted table in the terminal

### 5. Logging

- Logging is globally toggled ON/OFF (stored in the database config table or a `.env` / config file)
- When enabled:
  - A new log file is created per session: `usageapp-<YYYYMMDD-HHMMSS>.log`
  - Log file is stored in a `logs/` subdirectory alongside the database
  - Every action from options 1–4 (fetch, admin, view) is written to the active log file
  - Log entries include: timestamp, action type, provider name, result/error
- When disabled: no file is written; errors print to stderr only

---

## Application Flow

### Startup Flow

```
python llmusage.py
  │
  ├── Load config (DB path, logging state)
  ├── Connect to SQLite DB (create tables if first run)
  ├── If logging enabled → open/create log file usageapp-<timestamp>.log
  └── Display main menu
```

### Main Menu

```
LLM Usage Tracker
─────────────────
1. Fetch usage — select provider
2. Fetch usage — all providers
3. View usage report
4. Manage providers (Admin)
5. Toggle logging  [currently: ON/OFF]
6. Exit
```

### Flow: Fetch Usage (Single Provider)

```
Select provider → list numbered providers
  │
  ├── User picks number
  ├── App calls provider API with stored key/URL
  ├── Parse response → tokens_in, tokens_out, cost, balance
  ├── INSERT record into usage_records table
  ├── Print summary to terminal
  └── If logging ON → write entry to log file
```

### Flow: Fetch Usage (All Providers)

```
For each configured provider:
  ├── Attempt API call
  ├── On success → save record, print row
  └── On failure → log error, print warning, continue

Print aggregate summary table at end
```

### Flow: Manage Providers

```
Provider Admin Menu
───────────────────
1. List all providers
2. Add provider
3. Edit provider
4. Delete provider
5. Back

Add/Edit collects: name, api_url, api_key, display_label
Delete asks: "Delete <name>? [y/N]"
```

### Flow: Toggle Logging

```
Current state shown (ON/OFF)
  ├── Confirm toggle
  ├── Update config in DB
  └── If turning ON → immediately open new log file for this session
```

---

## Data Model (SQLite)

### Table: `providers`

| Column         | Type    | Notes                          |
|----------------|---------|--------------------------------|
| id             | INTEGER | Primary key, autoincrement     |
| name           | TEXT    | Unique short name (e.g. openai)|
| display_label  | TEXT    | Human-friendly label           |
| api_url        | TEXT    | Base URL or endpoint           |
| api_key        | TEXT    | Stored as-is (user's key)      |
| created_at     | TEXT    | ISO 8601 timestamp             |
| updated_at     | TEXT    | ISO 8601 timestamp             |

### Table: `usage_records`

| Column         | Type    | Notes                          |
|----------------|---------|--------------------------------|
| id             | INTEGER | Primary key, autoincrement     |
| provider_id    | INTEGER | FK → providers.id              |
| fetched_at     | TEXT    | ISO 8601 timestamp             |
| tokens_in      | INTEGER | Input tokens used              |
| tokens_out     | INTEGER | Output tokens used             |
| cost_usd       | REAL    | Estimated cost in USD          |
| balance_usd    | REAL    | Remaining credit/balance       |
| raw_response   | TEXT    | JSON blob of API response      |

### Table: `config`

| Column  | Type | Notes                          |
|---------|------|--------------------------------|
| key     | TEXT | Primary key (e.g. logging)     |
| value   | TEXT | String value                   |

---

## Provider API Integration

Each provider requires a dedicated adapter module. Known endpoints:

| Provider    | Usage Endpoint (approximate)                         |
|-------------|------------------------------------------------------|
| OpenAI      | `GET /v1/usage` (dashboard API key required)         |
| Anthropic   | `GET /v1/usage` or account API                       |
| Gemini      | Google Cloud billing API / AI Studio quota           |
| OpenRouter  | `GET /api/v1/auth/key` (returns usage + balance)     |
| DeepSeek    | Provider account API                                 |

Adapters implement a common interface:
```python
def fetch_usage(api_key: str, api_url: str) -> dict:
    # returns: tokens_in, tokens_out, cost_usd, balance_usd
```

---

## Project Structure

```
llmusage/
├── llmusage.py          # Entry point, menu loop
├── db.py                # SQLite connection, schema init, queries
├── logger.py            # Log file management
├── config.py            # Config read/write (from DB config table)
├── providers/
│   ├── base.py          # Abstract adapter interface
│   ├── openai.py
│   ├── anthropic.py
│   ├── gemini.py
│   ├── openrouter.py
│   └── deepseek.py
├── commands/
│   ├── fetch.py         # Fetch single / all providers
│   ├── report.py        # View usage report
│   └── admin.py         # Provider CRUD
├── data/
│   └── llmusage.db      # SQLite database (created at runtime)
├── logs/                # Log files (created at runtime)
├── requirements.txt
└── planning/
    ├── PLAN.md
    └── requirement.md
```

---

## Development Plan

### Phase 1 — Foundation
- [ ] Set up project structure and `requirements.txt`
- [ ] Implement `db.py`: schema creation, connection helper
- [ ] Implement `config.py`: read/write config key-value pairs
- [ ] Implement `logger.py`: session log file open/write/close
- [ ] Stub `llmusage.py` main menu loop

### Phase 2 — Provider Admin
- [ ] Implement `commands/admin.py`: list, add, edit, delete providers
- [ ] Wire into main menu (option 4)
- [ ] Manual test: add OpenRouter + OpenAI providers via CLI

### Phase 3 — Provider Adapters
- [ ] Implement `providers/base.py` abstract interface
- [ ] Implement adapters: OpenRouter (simplest), OpenAI, Anthropic, DeepSeek, Gemini
- [ ] Unit-test each adapter with a real API key in isolation

### Phase 4 — Fetch & Store
- [ ] Implement `commands/fetch.py`: single-provider and all-providers flows
- [ ] Save records to `usage_records` table
- [ ] Wire into main menu (options 1 & 2)

### Phase 5 — Reporting
- [ ] Implement `commands/report.py`: filter by provider / date, aggregate totals
- [ ] Display formatted table using `rich` or `tabulate`
- [ ] Wire into main menu (option 3)

### Phase 6 — Logging Integration
- [ ] Connect `logger.py` to all command actions
- [ ] Implement toggle (option 5 in main menu)
- [ ] Verify log file naming and content format

### Phase 7 — Polish & Packaging
- [ ] Error handling and user-friendly messages for failed API calls
- [ ] `--help` and optional CLI argument mode (e.g. `llmusage fetch --provider openai`)
- [ ] `requirements.txt` finalized (`requests`, `rich` or `tabulate`, `python-dotenv`)
- [ ] Final end-to-end test across all providers

---

## Dependencies (proposed)

| Package        | Purpose                          |
|----------------|----------------------------------|
| `requests`     | HTTP calls to provider APIs      |
| `rich`         | Terminal tables and formatting   |
| `python-dotenv`| Optional .env support            |

Python 3.9+ assumed. No external database server required (SQLite only).
