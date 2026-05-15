import sqlite3
import os
from datetime import datetime, timezone

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "llmusage.db")


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with get_connection() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS providers (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                name          TEXT    NOT NULL UNIQUE,
                display_label TEXT,
                api_url       TEXT,
                api_key       TEXT,
                created_at    TEXT    NOT NULL,
                updated_at    TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS usage_records (
                id           INTEGER PRIMARY KEY AUTOINCREMENT,
                provider_id  INTEGER NOT NULL REFERENCES providers(id) ON DELETE CASCADE,
                fetched_at   TEXT    NOT NULL,
                tokens_in    INTEGER DEFAULT 0,
                tokens_out   INTEGER DEFAULT 0,
                cost_usd     REAL    DEFAULT 0.0,
                balance_usd  REAL,
                raw_response TEXT
            );

            CREATE TABLE IF NOT EXISTS config (
                key   TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            INSERT OR IGNORE INTO config (key, value) VALUES ('logging', 'off');
        """)


def now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ── Provider queries ──────────────────────────────────────────────────────────

def provider_list() -> list[sqlite3.Row]:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM providers ORDER BY name"
        ).fetchall()


def provider_get(provider_id: int) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM providers WHERE id = ?", (provider_id,)
        ).fetchone()


def provider_get_by_name(name: str) -> sqlite3.Row | None:
    with get_connection() as conn:
        return conn.execute(
            "SELECT * FROM providers WHERE name = ?", (name,)
        ).fetchone()


def provider_add(name: str, display_label: str, api_url: str, api_key: str) -> int:
    ts = now_iso()
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO providers (name, display_label, api_url, api_key, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (name.strip().lower(), display_label.strip(), api_url.strip(), api_key.strip(), ts, ts),
        )
        return cur.lastrowid


def provider_update(provider_id: int, name: str, display_label: str, api_url: str, api_key: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE providers SET name=?, display_label=?, api_url=?, api_key=?, updated_at=? "
            "WHERE id=?",
            (name.strip().lower(), display_label.strip(), api_url.strip(), api_key.strip(), now_iso(), provider_id),
        )


def provider_delete(provider_id: int) -> None:
    with get_connection() as conn:
        conn.execute("DELETE FROM providers WHERE id = ?", (provider_id,))


# ── Usage record queries ──────────────────────────────────────────────────────

def record_insert(provider_id: int, tokens_in: int, tokens_out: int,
                  cost_usd: float, balance_usd: float | None, raw_response: str) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            "INSERT INTO usage_records "
            "(provider_id, fetched_at, tokens_in, tokens_out, cost_usd, balance_usd, raw_response) "
            "VALUES (?, ?, ?, ?, ?, ?, ?)",
            (provider_id, now_iso(), tokens_in, tokens_out, cost_usd, balance_usd, raw_response),
        )
        return cur.lastrowid


def records_for_report(provider_id: int | None = None,
                       days: int | None = None) -> list[sqlite3.Row]:
    clauses = []
    params: list = []

    if provider_id is not None:
        clauses.append("r.provider_id = ?")
        params.append(provider_id)

    if days is not None:
        clauses.append("r.fetched_at >= datetime('now', ?)")
        params.append(f"-{days} days")

    where = ("WHERE " + " AND ".join(clauses)) if clauses else ""
    sql = f"""
        SELECT r.*, p.name AS provider_name, p.display_label
        FROM usage_records r
        JOIN providers p ON p.id = r.provider_id
        {where}
        ORDER BY r.fetched_at DESC
    """
    with get_connection() as conn:
        return conn.execute(sql, params).fetchall()


# ── Config queries ────────────────────────────────────────────────────────────

def config_get(key: str, default: str = "") -> str:
    with get_connection() as conn:
        row = conn.execute("SELECT value FROM config WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default


def config_set(key: str, value: str) -> None:
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO config (key, value) VALUES (?, ?) "
            "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
            (key, value),
        )
