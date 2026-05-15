import json
from rich.console import Console
from rich.table import Table
from rich import box
import db
import logger
from providers import get_adapter

console = Console()


def _pick_provider() -> db.sqlite3.Row | None:
    rows = db.provider_list()
    if not rows:
        console.print("[yellow]No providers configured. Add one via Admin menu.[/yellow]")
        return None

    t = Table(box=box.SIMPLE, show_header=True, header_style="bold")
    t.add_column("#", justify="right", width=4)
    t.add_column("Name")
    t.add_column("Label")
    for i, r in enumerate(rows, 1):
        t.add_row(str(i), r["name"], r["display_label"] or "")
    console.print(t)

    raw = input("  Select provider number (0=cancel): ").strip()
    if raw == "0" or not raw:
        return None
    try:
        idx = int(raw) - 1
        return rows[idx]
    except (ValueError, IndexError):
        console.print("[red]Invalid selection.[/red]")
        return None


def _do_fetch(row: db.sqlite3.Row) -> bool:
    name = row["name"]
    console.print(f"  Fetching [bold]{name}[/bold]...", end=" ")
    try:
        adapter = get_adapter(name, row["api_key"], row["api_url"] or "")
        result = adapter.fetch_usage()
        db.record_insert(
            provider_id=row["id"],
            tokens_in=result.tokens_in,
            tokens_out=result.tokens_out,
            cost_usd=result.cost_usd,
            balance_usd=result.balance_usd,
            raw_response=result.raw_response,
        )
        balance_str = f"${result.balance_usd:.4f}" if result.balance_usd is not None else "N/A"
        console.print(
            f"[green]OK[/green]  "
            f"in={result.tokens_in:,}  out={result.tokens_out:,}  "
            f"cost=${result.cost_usd:.6f}  balance={balance_str}"
        )
        logger.log("fetch.success", provider=name,
                   detail=f"tokens_in={result.tokens_in} tokens_out={result.tokens_out} "
                          f"cost={result.cost_usd} balance={result.balance_usd}")
        return True
    except Exception as e:
        console.print(f"[red]FAILED[/red] — {e}")
        logger.log("fetch.error", provider=name, detail=str(e))
        return False


def fetch_single() -> None:
    row = _pick_provider()
    if row:
        _do_fetch(row)


def fetch_all() -> None:
    rows = db.provider_list()
    if not rows:
        console.print("[yellow]No providers configured.[/yellow]")
        return

    console.print(f"\nFetching usage for [bold]{len(rows)}[/bold] provider(s)...\n")
    ok = fail = 0
    for row in rows:
        if _do_fetch(row):
            ok += 1
        else:
            fail += 1

    console.print(f"\n  Done — [green]{ok} succeeded[/green]"
                  + (f", [red]{fail} failed[/red]" if fail else ""))
    logger.log("fetch_all.complete", detail=f"ok={ok} failed={fail}")
