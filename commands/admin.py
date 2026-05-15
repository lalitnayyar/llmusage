from rich.console import Console
from rich.table import Table
from rich import box
import db
import logger

console = Console()

KNOWN_PROVIDERS = ["openai", "anthropic", "gemini", "openrouter", "deepseek", "other"]


def run() -> None:
    while True:
        console.print("\n[bold cyan]Provider Admin[/bold cyan]")
        console.print("  1. List all providers")
        console.print("  2. Add provider")
        console.print("  3. Edit provider")
        console.print("  4. Delete provider")
        console.print("  5. Back")
        choice = input("\nSelect: ").strip()

        if choice == "1":
            _list_providers()
        elif choice == "2":
            _add_provider()
        elif choice == "3":
            _edit_provider()
        elif choice == "4":
            _delete_provider()
        elif choice == "5":
            break
        else:
            console.print("[yellow]Invalid choice.[/yellow]")


def _list_providers() -> None:
    rows = db.provider_list()
    if not rows:
        console.print("[yellow]No providers configured.[/yellow]")
        return

    t = Table(box=box.SIMPLE_HEAVY, show_header=True, header_style="bold magenta")
    t.add_column("ID", justify="right", width=4)
    t.add_column("Name", min_width=12)
    t.add_column("Label", min_width=16)
    t.add_column("API URL", min_width=30)
    t.add_column("API Key", min_width=20)
    t.add_column("Updated", min_width=20)

    for r in rows:
        key = r["api_key"] or ""
        masked = key[:4] + "****" + key[-4:] if len(key) > 8 else "****"
        t.add_row(str(r["id"]), r["name"], r["display_label"] or "",
                  r["api_url"] or "", masked, r["updated_at"])

    console.print(t)
    logger.log("admin.list_providers", detail=f"count={len(rows)}")


def _prompt_provider_fields(defaults: dict | None = None) -> dict | None:
    d = defaults or {}

    console.print(f"\n  Known provider names: {', '.join(KNOWN_PROVIDERS)}")
    name = input(f"  Name [{d.get('name', '')}]: ").strip() or d.get("name", "")
    if not name:
        console.print("[red]Name is required.[/red]")
        return None

    label = input(f"  Display label [{d.get('display_label', '')}]: ").strip() or d.get("display_label", "")
    url = input(f"  API URL [{d.get('api_url', '')}]: ").strip() or d.get("api_url", "")
    key = input(f"  API Key [{('****' if d.get('api_key') else '')}]: ").strip() or d.get("api_key", "")

    return {"name": name, "display_label": label, "api_url": url, "api_key": key}


def _add_provider() -> None:
    console.print("\n[bold]Add Provider[/bold]")
    fields = _prompt_provider_fields()
    if not fields:
        return
    try:
        pid = db.provider_add(fields["name"], fields["display_label"],
                              fields["api_url"], fields["api_key"])
        console.print(f"[green]Provider '{fields['name']}' added (id={pid}).[/green]")
        logger.log("admin.add_provider", provider=fields["name"], detail=f"id={pid}")
    except Exception as e:
        console.print(f"[red]Error:[/red] {e}")
        logger.log("admin.add_provider.error", provider=fields["name"], detail=str(e))


def _edit_provider() -> None:
    _list_providers()
    raw = input("\n  Enter provider ID to edit (0=cancel): ").strip()
    if raw == "0" or not raw:
        return
    try:
        pid = int(raw)
    except ValueError:
        console.print("[red]Invalid ID.[/red]")
        return

    row = db.provider_get(pid)
    if not row:
        console.print(f"[red]No provider with id={pid}.[/red]")
        return

    console.print(f"\n[bold]Editing '{row['name']}'[/bold] — press Enter to keep current value")
    fields = _prompt_provider_fields(dict(row))
    if not fields:
        return
    db.provider_update(pid, fields["name"], fields["display_label"],
                       fields["api_url"], fields["api_key"])
    console.print(f"[green]Provider '{fields['name']}' updated.[/green]")
    logger.log("admin.edit_provider", provider=fields["name"], detail=f"id={pid}")


def _delete_provider() -> None:
    _list_providers()
    raw = input("\n  Enter provider ID to delete (0=cancel): ").strip()
    if raw == "0" or not raw:
        return
    try:
        pid = int(raw)
    except ValueError:
        console.print("[red]Invalid ID.[/red]")
        return

    row = db.provider_get(pid)
    if not row:
        console.print(f"[red]No provider with id={pid}.[/red]")
        return

    confirm = input(f"  Delete '{row['name']}'? [y/N]: ").strip().lower()
    if confirm == "y":
        db.provider_delete(pid)
        console.print(f"[green]Provider '{row['name']}' deleted.[/green]")
        logger.log("admin.delete_provider", provider=row["name"], detail=f"id={pid}")
    else:
        console.print("Cancelled.")
