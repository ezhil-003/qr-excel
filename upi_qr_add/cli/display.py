"""Rich display layers and render functions for the CLI."""

from __future__ import annotations

from pathlib import Path

from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn
import time

from .ascii_ui import ASCII_LOGO, BOOT_STEPS
from ..core.models import ProcessSummary
from ..database.logger import SQLiteLogger, find_latest_session_db

console = Console(highlight=False)

def show_error(message: str) -> None:
    """Standardized error display hook."""
    console.print(f"  [bold red][!][/] {message}")

def print_raw(msg: str) -> None:
    console.print(msg)

def render_boot_sequence() -> None:
    """Renders a fancy, technical-themed system boot sequence."""
    console.print("\n")
    
    with Progress(
        SpinnerColumn(spinner_name="dots12", style="bold cyan"),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(bar_width=40, style="blue", complete_style="bold cyan"),
        TaskProgressColumn(),
        console=console,
        transient=True,
    ) as progress:
        boot_task = progress.add_task("[bold white]CORE SYSTEM BOOTING...", total=100)
        
        for p, msg in BOOT_STEPS:
            time.sleep(0.4)
            progress.update(boot_task, completed=p, description=msg)
        
        time.sleep(0.3)
    
    console.print("\n")

def render_title(version: str) -> None:
    console.print("\n")
    logo = Text(ASCII_LOGO, style="bold cyan")
    info = Text.from_markup(
        "[bold yellow][BOOT][/]   [white]CORE SYSTEM INITIALIZED[/]       - Advanced CLI for Bulk UPI QR Code Generation\n"
        "[bold yellow][INIT][/]   [white]Excel Engine[/]          : [bold green]READY[/] - Processing standard .xlsx workbooks\n"
        "[bold yellow][LOAD][/]   [white]QR Generator[/]          : [bold green]READY[/] - Dynamic Payload Assembly / Asset Linking\n"
        "[bold yellow][READY][/]  [white]Modes[/]                 : [bold cyan]EMBED | HYPERLINK[/]\n"
        "[bold yellow][DB][/]     [white]Session Logging[/]       : [bold green]ACTIVE[/]- SQLite-backed tracking & resume protection"
    )
    panel = Panel(
        Group(logo, Text(""), info),
        box=box.DOUBLE,
        border_style="blue",
        padding=(0, 2),
        title="[bold white]UPI QR CLI[/]",
        subtitle=f"[bold white]v{version} Engine Ready[/]",
        width=110
    )
    console.print(panel)


def render_instruction(label: str, rules: str, example: str) -> None:
    text = Text.from_markup(f"[bold cyan]Rules   :[/] {rules}\n[bold cyan]Example :[/] {example}")
    panel = Panel(text, title=f"[bold yellow]{label}[/]", border_style="cyan", padding=(0, 2), width=90)
    console.print("\n")
    console.print(panel)


def render_custom_billing_header() -> None:
    text = Text.from_markup(
        "VPA is built dynamically per row as: [bold cyan]<prefix><column_value><suffix>[/]\n"
        "e.g.  [bold yellow]hello.<InvoiceID>@okaxis[/]"
    )
    panel = Panel(text, title="[bold magenta]Custom Billing Details[/]", border_style="magenta", padding=(0, 2), width=90)
    console.print("\n")
    console.print(panel)


def print_summary(summary: ProcessSummary, db_path: Path) -> None:
    table = Table(box=box.MINIMAL_DOUBLE_HEAD, show_header=False, width=90)
    table.add_column("Property", style="bold cyan")
    table.add_column("Value", style="bold white")

    table.add_row("Status", f"[bold green]{summary.status}[/]" if summary.status == "completed" else f"[bold yellow]{summary.status}[/]")
    table.add_row("Session ID", summary.session_id)
    table.add_row("Total Rows Parsed", str(summary.total_rows))
    table.add_row("Successful Generates", f"[green]{summary.successful}[/]")
    table.add_row("Failed Generates", f"[red]{summary.failed_total}[/]" if summary.failed_total > 0 else "[green]0[/]")
    table.add_row("Result Excel File", str(summary.output_file))

    if summary.resumed_from is not None:
        table.add_row("Resumed From Row", str(summary.resumed_from + 1))
    if summary.error_message:
        table.add_row("System Error", f"[bold red]{summary.error_message}[/]")
    table.add_row("Database Log File", str(db_path))

    panel = Panel(table, title="[bold green]Batch Run Summary[/]", border_style="green", padding=(0, 2), width=96)
    console.print("\n")
    console.print(panel)
    console.print("\n")


def show_last_run_errors(last_session_db: Path | None) -> None:
    target_db = last_session_db if last_session_db and last_session_db.exists() else find_latest_session_db()
    if target_db is None:
        console.print("\n  [bold yellow][!] No session logs found in the system.[/]\n")
        return

    with SQLiteLogger(target_db) as logger:
        state = logger.get_session_state()
        failed_rows = logger.get_failed_logs(session_id=str(state["session_id"]))
        session_events = logger.get_session_events()

    info_text = f"[bold cyan]DB Location:[/] {target_db}"
    panel = Panel(info_text, title=f"[bold red]Session Diagnostics ID: {state['session_id']} | Status: {state['status']}[/]", border_style="red", padding=(0, 2), width=100)
    console.print("\n")
    console.print(panel)
    console.print()

    if failed_rows:
        table = Table(title="[bold red]Row-Level Processing Failures[/]", box=box.SIMPLE, width=100)
        table.add_column("Timestamp", style="dim", no_wrap=True)
        table.add_column("Row Index", style="bold yellow")
        table.add_column("Failure Step", style="cyan")
        table.add_column("Error Category", style="bold red")
        table.add_column("Detailed Message", style="white")

        for row in failed_rows:
            table.add_row(
                str(row['timestamp'] or ''),
                str(row['row_index'] or ''),
                str(row['step'] or ''),
                str(row['error_type'] or ''),
                str(row['error_message'] or '')
            )
        console.print(table)
    else:
        console.print("  [bold green][OK] Database check complete: No failed row entries found in this session.[/]\n")

    failed_events = [e for e in session_events if e["status"] == "failed"]
    if failed_events:
        table = Table(title="[bold red]System-Level Core Errors[/]", box=box.SIMPLE, width=100)
        table.add_column("Timestamp", style="dim", no_wrap=True)
        table.add_column("Failure Step", style="cyan")
        table.add_column("Error Category", style="bold red")
        table.add_column("Detailed Message", style="white")

        for event in failed_events:
            table.add_row(
                str(event['timestamp'] or ''),
                str(event['step'] or ''),
                str(event['error_type'] or ''),
                str(event['error_message'] or '')
            )
        console.print(table)
        console.print()
