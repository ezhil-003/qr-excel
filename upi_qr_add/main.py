from __future__ import annotations

import os
from pathlib import Path

import typer
from prompt_toolkit.shortcuts import radiolist_dialog
from rich import box
from rich.columns import Columns
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from upi_qr_add.core import ProcessConfig, ProcessSummary, QRMode, process_workbook
    from upi_qr_add.logger import (
        SQLiteLogger,
        archive_or_delete_completed_sessions,
        find_latest_session_db,
        find_resumable_session_for_input,
        init_session_db_from_template,
    )
    from upi_qr_add.utils import make_session_id
else:
    from .core import ProcessConfig, ProcessSummary, QRMode, process_workbook
    from .logger import (
        SQLiteLogger,
        archive_or_delete_completed_sessions,
        find_latest_session_db,
        find_resumable_session_for_input,
        init_session_db_from_template,
    )
    from .utils import make_session_id

app = typer.Typer(add_completion=False, no_args_is_help=False)
console = Console()


def _render_title() -> None:
    banner = Text()
    banner.append("UPI QR ADD", style="bold magenta")
    banner.append("\nProduction CLI for Excel Payment QR Automation", style="cyan")
    panel = Panel(
        banner,
        title="[bold white]v0.1[/bold white]",
        border_style="bright_magenta",
        box=box.DOUBLE_EDGE,
        expand=False,
    )
    tips = Panel(
        "Use arrow keys in menus.\nUse Ctrl+C during processing to pause and return to menu.",
        title="Operator Notes",
        border_style="cyan",
        box=box.ROUNDED,
        expand=False,
    )
    console.print(Columns([panel, tips], equal=False, expand=True))


def _render_instruction(label: str, rules: str, example: str) -> None:
    body = (
        f"[bold]{label}[/bold]\n"
        f"[cyan]Rules:[/cyan] {rules}\n"
        f"[cyan]Example:[/cyan] {example}"
    )
    console.print(Panel.fit(body, border_style="blue", box=box.SQUARE))


def _ask_input_path() -> Path:
    while True:
        _render_instruction(
            "Input Excel File",
            "Provide an existing .xlsx file path. First sheet will be processed.",
            "/Users/you/Documents/orders.xlsx",
        )
        raw_path = Prompt.ask("Path to input Excel file (.xlsx)").strip()
        input_path = Path(raw_path).expanduser()
        if not input_path.exists():
            console.print("[red]File does not exist. Please try again.[/red]")
            continue
        if input_path.suffix.lower() != ".xlsx":
            console.print("[red]Only .xlsx files are supported.[/red]")
            continue
        return input_path


def _ask_mode() -> QRMode:
    _render_instruction(
        "QR Mode",
        "Choose how payment_qr is written in Excel.",
        "Embed mode is recommended for single-file sharing.",
    )
    selected = radiolist_dialog(
        title="QR Mode",
        text="Use ↑/↓ and Enter",
        values=[
            (QRMode.EMBED.value, "Embed QR image directly in Excel cell (recommended)"),
            (QRMode.HYPERLINK.value, "Save QR images in subfolder and insert hyperlink"),
        ],
    ).run()
    if selected == QRMode.HYPERLINK.value:
        return QRMode.HYPERLINK
    return QRMode.EMBED


def _ask_vpa() -> str:
    while True:
        _render_instruction(
            "Merchant VPA",
            "Non-empty UPI ID in provider format.",
            "merchant@okaxis",
        )
        value = Prompt.ask("Merchant VPA (UPI ID)").strip()
        if value:
            return value
        console.print("[red]Merchant VPA cannot be empty.[/red]")


def _ask_payee_name() -> str:
    while True:
        _render_instruction(
            "Payee Name",
            "Non-empty display name used in UPI payment request.",
            "Ezhil Sivaraj",
        )
        value = Prompt.ask("Payee Name").strip()
        if value:
            return value
        console.print("[red]Payee Name cannot be empty.[/red]")


def _ask_note() -> str:
    _render_instruction(
        "Transaction Note",
        "Optional free text. Keep it short and clear.",
        "Payment for order",
    )
    return Prompt.ask("Transaction Note", default="Payment for order").strip()


def _choose_main_menu() -> str:
    selected = radiolist_dialog(
        title="Main Menu",
        text="Use ↑/↓ and Enter",
        values=[
            ("start", "Start New Run"),
            ("view_errors", "View Last Run Errors"),
            ("quit", "Quit"),
        ],
    ).run()
    return selected or "quit"


def _resolve_session_db(input_path: Path) -> tuple[Path, bool]:
    resumable = find_resumable_session_for_input(input_path)
    if resumable is not None and resumable.exists():
        return resumable, True
    session_id = make_session_id()
    return init_session_db_from_template(session_id), False


def _print_summary(summary, db_path: Path) -> None:
    table = Table(title="Run Summary", show_header=False, box=box.SIMPLE_HEAVY)
    table.add_row("Status", summary.status)
    table.add_row("Session ID", summary.session_id)
    table.add_row("Total rows", str(summary.total_rows))
    table.add_row("Successful", str(summary.successful))
    table.add_row("Failed", str(summary.failed_total))
    table.add_row("Output file", str(summary.output_file))
    if summary.resumed_from is not None:
        table.add_row("Resumed from row", str(summary.resumed_from + 1))
    if summary.error_message:
        table.add_row("Setup Error", summary.error_message)
    table.add_row("Session DB", str(db_path))
    console.print(table)


def _show_last_run_errors(last_session_db: Path | None) -> None:
    target_db = last_session_db if last_session_db and last_session_db.exists() else find_latest_session_db()
    if target_db is None:
        console.print("[yellow]No session logs found.[/yellow]")
        return

    with SQLiteLogger(target_db) as logger:
        state = logger.get_session_state()
        failed_rows = logger.get_failed_logs(session_id=str(state["session_id"]))
        session_events = logger.get_session_events()

    console.print(
        Panel.fit(
            f"Session: [bold]{state['session_id']}[/bold]\nStatus: [bold]{state['status']}[/bold]\nDB: {target_db}",
            border_style="magenta",
        )
    )

    if failed_rows:
        table = Table(title="Row-Level Failures", box=box.MINIMAL_DOUBLE_HEAD)
        table.add_column("Timestamp")
        table.add_column("Row")
        table.add_column("Step")
        table.add_column("Error Type")
        table.add_column("Message")
        table.add_column("Amount")
        table.add_column("Txn ID")
        for row in failed_rows:
            table.add_row(
                str(row["timestamp"] or ""),
                str(row["row_index"] or ""),
                str(row["step"] or ""),
                str(row["error_type"] or ""),
                str(row["error_message"] or ""),
                str(row["amount"] or ""),
                str(row["txn_id"] or ""),
            )
        console.print(table)
    else:
        console.print("[green]No failed row entries in the selected session.[/green]")

    failed_events = [event for event in session_events if event["status"] == "failed"]
    if failed_events:
        event_table = Table(title="Session-Level Errors", box=box.SIMPLE)
        event_table.add_column("Timestamp")
        event_table.add_column("Step")
        event_table.add_column("Error Type")
        event_table.add_column("Message")
        for event in failed_events:
            event_table.add_row(
                str(event["timestamp"] or ""),
                str(event["step"] or ""),
                str(event["error_type"] or ""),
                str(event["error_message"] or ""),
            )
        console.print(event_table)


def _run_single_session() -> tuple[Path, ProcessSummary]:
    input_path = _ask_input_path()
    vpa = _ask_vpa()
    payee_name = _ask_payee_name()
    note = _ask_note()
    mode = _ask_mode()

    session_db, resumed = _resolve_session_db(input_path)
    if resumed:
        console.print(f"[yellow]Resuming interrupted session from:[/yellow] {session_db}")

    logo_path_env = os.getenv("UPI_QR_LOGO_PATH", "").strip()
    logo_path = Path(logo_path_env).expanduser() if logo_path_env else None

    config = ProcessConfig(
        vpa=vpa,
        payee_name=payee_name,
        note=note,
        mode=mode,
        logo_path=logo_path,
        db_path=session_db,
    )
    summary = process_workbook(input_path, config)
    return session_db, summary


def _run_interactive() -> None:
    _render_title()
    last_session_db: Path | None = find_latest_session_db()

    while True:
        choice = _choose_main_menu()
        if choice == "quit":
            archive_or_delete_completed_sessions()
            console.print("[bold cyan]Session ended.[/bold cyan]")
            return

        if choice == "view_errors":
            _show_last_run_errors(last_session_db)
            continue

        if choice == "start":
            cleaned = archive_or_delete_completed_sessions()
            if cleaned > 0:
                console.print(f"[cyan]Cleared {cleaned} completed session log file(s).[/cyan]")

            session_db = None
            try:
                session_db, summary = _run_single_session()
                last_session_db = session_db
                _print_summary(summary, session_db)
            except KeyboardInterrupt:
                if session_db is not None:
                    last_session_db = session_db
                console.print("[yellow]Interrupted by user. Returned to main menu.[/yellow]")
            except Exception as exc:  # pragma: no cover - defensive guard for unexpected errors.
                console.print(f"[red]Unexpected error:[/red] {exc}")


@app.callback(invoke_without_command=True)
def entrypoint(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _run_interactive()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
