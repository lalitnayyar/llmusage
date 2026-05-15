from rich.console import Console
from rich.table import Table
from rich import box
import db
import logger

console = Console()


def run() -> None:
    console.print("\n[bold cyan]Usage Report[/bold cyan]")
    console.print("  1. All records (last 30 days)")
    console.print("  2. Filter by provider")
    console.print("  3. Today only")
    console.print("  4. Custom date range (last N days)")
    console.print("  5. All time")
    choice = input("\nSelect: ").strip()

    provider_id = None
    days = None

    if choice == "1":
        days = 30
    elif choice == "2":
        rows = db.provider_list()
        if not rows:
            console.print("[yellow]No providers configured.[/yellow]")
            return
        for r in rows:
            console.print(f"  {r['id']}. {r['name']}")
        raw = input("  Provider ID: ").strip()
        try:
            provider_id = int(raw)
        except ValueError:
            console.print("[red]Invalid ID.[/red]")
            return
        days = 30
    elif choice == "3":
        days = 1
    elif choice == "4":
        raw = input("  Last N days: ").strip()
        try:
            days = int(raw)
        except ValueError:
            console.print("[red]Invalid number.[/red]")
            return
    elif choice == "5":
        days = None
    else:
        console.print("[yellow]Invalid choice.[/yellow]")
        return

    records = db.records_for_report(provider_id=provider_id, days=days)

    if not records:
        console.print("[yellow]No records found.[/yellow]")
        return

    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("Fetched At", min_width=20)
    t.add_column("Provider", min_width=12)
    t.add_column("Tokens In", justify="right", min_width=10)
    t.add_column("Tokens Out", justify="right", min_width=10)
    t.add_column("Cost (USD)", justify="right", min_width=12)
    t.add_column("Balance (USD)", justify="right", min_width=13)

    total_in = total_out = 0
    total_cost = 0.0

    for r in records:
        balance = f"${r['balance_usd']:.4f}" if r["balance_usd"] is not None else "—"
        t.add_row(
            r["fetched_at"],
            r["provider_name"],
            f"{r['tokens_in']:,}",
            f"{r['tokens_out']:,}",
            f"${r['cost_usd']:.6f}",
            balance,
        )
        total_in += r["tokens_in"] or 0
        total_out += r["tokens_out"] or 0
        total_cost += r["cost_usd"] or 0.0

    t.add_section()
    t.add_row("[bold]TOTAL[/bold]", "", f"[bold]{total_in:,}[/bold]",
              f"[bold]{total_out:,}[/bold]", f"[bold]${total_cost:.6f}[/bold]", "")

    console.print(t)
    console.print(f"  {len(records)} record(s) shown\n")
    logger.log("report.view", detail=f"records={len(records)} days={days} provider_id={provider_id}")
