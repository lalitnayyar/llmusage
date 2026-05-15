#!/usr/bin/env python3
"""LLM Usage Tracker — command-line application."""

import sys
import os

# Ensure project root is on the path so sub-modules resolve correctly
sys.path.insert(0, os.path.dirname(__file__))

from rich.console import Console
import db
import config
import logger
from commands import admin, fetch, report

console = Console()


def _toggle_logging() -> None:
    current = config.logging_enabled()
    state = "ON" if current else "OFF"
    confirm = input(f"  Logging is currently {state}. Toggle? [y/N]: ").strip().lower()
    if confirm != "y":
        console.print("  Cancelled.")
        return

    new_state = not current
    config.set_logging(new_state)

    if new_state:
        log_path = logger.open_session_log()
        console.print(f"[green]Logging enabled.[/green] Log file: {log_path}")
    else:
        logger.log("logging.disabled")
        logger.close_session_log()
        console.print("[yellow]Logging disabled.[/yellow]")


def main() -> None:
    db.init_db()

    # Auto-open log file if logging was previously enabled
    if config.logging_enabled():
        log_path = logger.open_session_log()
        console.print(f"[dim]Logging active → {log_path}[/dim]")

    logger.log("app.start")

    try:
        while True:
            log_status = "[green]ON[/green]" if config.logging_enabled() else "[red]OFF[/red]"
            console.print(f"\n[bold cyan]LLM Usage Tracker[/bold cyan]  "
                          f"[dim]logging: {log_status}[/dim]")
            console.print("─" * 40)
            console.print("  1. Fetch usage — select provider")
            console.print("  2. Fetch usage — all providers")
            console.print("  3. View usage report")
            console.print("  4. Manage providers (Admin)")
            console.print(f"  5. Toggle logging  [logging: {log_status}]")
            console.print("  6. Exit")

            choice = input("\nSelect: ").strip()

            if choice == "1":
                logger.log("menu.fetch_single")
                fetch.fetch_single()
            elif choice == "2":
                logger.log("menu.fetch_all")
                fetch.fetch_all()
            elif choice == "3":
                logger.log("menu.report")
                report.run()
            elif choice == "4":
                logger.log("menu.admin")
                admin.run()
            elif choice == "5":
                _toggle_logging()
            elif choice == "6":
                break
            else:
                console.print("[yellow]Invalid choice — enter 1–6.[/yellow]")

    except KeyboardInterrupt:
        console.print("\n\n[dim]Interrupted.[/dim]")
    finally:
        logger.log("app.exit")
        logger.close_session_log()
        console.print("[dim]Goodbye.[/dim]")


if __name__ == "__main__":
    main()
