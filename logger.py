import os
from datetime import datetime, timezone
from typing import IO

LOGS_DIR = os.path.join(os.path.dirname(__file__), "logs")

_log_file: IO | None = None
_log_path: str | None = None


def open_session_log() -> str:
    global _log_file, _log_path
    os.makedirs(LOGS_DIR, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    _log_path = os.path.join(LOGS_DIR, f"usageapp-{ts}.log")
    _log_file = open(_log_path, "a", encoding="utf-8")
    _write(f"Session started — log file: {_log_path}")
    return _log_path


def close_session_log() -> None:
    global _log_file
    if _log_file:
        _write("Session ended")
        _log_file.close()
        _log_file = None


def log(action: str, provider: str = "", detail: str = "") -> None:
    if _log_file is None:
        return
    parts = [action]
    if provider:
        parts.append(f"provider={provider}")
    if detail:
        parts.append(detail)
    _write(" | ".join(parts))


def _write(message: str) -> None:
    if _log_file:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        _log_file.write(f"[{ts}] {message}\n")
        _log_file.flush()
