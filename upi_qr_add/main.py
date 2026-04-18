from __future__ import annotations

import os
import sys
from pathlib import Path

import typer
from prompt_toolkit import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import Window
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.styles import Style
from rich import box
from rich.console import Console, Group
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from upi_qr_add.core import BillingMode, ProcessConfig, ProcessSummary, QRMode, process_workbook
    from upi_qr_add.logger import (
        SQLiteLogger,
        archive_or_delete_completed_sessions,
        find_latest_session_db,
        find_resumable_session_for_input,
        init_session_db_from_template,
    )
    from upi_qr_add.utils import make_session_id
else:
    from .core import BillingMode, ProcessConfig, ProcessSummary, QRMode, process_workbook
    from .logger import (
        SQLiteLogger,
        archive_or_delete_completed_sessions,
        find_latest_session_db,
        find_resumable_session_for_input,
        init_session_db_from_template,
    )
    from .utils import make_session_id

app = typer.Typer(add_completion=False, no_args_is_help=False)
console = Console(highlight=False)

ASCII_LOGO = r"""
  ░██████   ░█████████                ░██████████ ░██    ░██   ░██████  ░██████████ ░██    
 ░██   ░██  ░██     ░██               ░██          ░██  ░██   ░██   ░██ ░██         ░██    
 ░██     ░██ ░██     ░██               ░██           ░██░██   ░██        ░██         ░██    
 ░██     ░██ ░█████████     ░██████    ░█████████     ░███    ░██        ░█████████  ░██    
 ░██     ░██ ░██   ░██                 ░██           ░██░██   ░██        ░██         ░██    
  ░██   ░██  ░██    ░██                ░██          ░██  ░██   ░██   ░██ ░██         ░██    
   ░██████   ░██     ░██               ░██████████ ░██    ░██   ░██████  ░██████████ ░████ 
"""


def ascii_select(title: str, options: list[tuple[str, str]], default_index: int = 0) -> str:
    """
    Vite-style inline select with dot highlighter.
    Returns the value (key) of the selected option.

    options: list of (value, label) tuples
    """
    state = {"idx": default_index}

    def get_tokens():
        lines = []
        lines.append(("class:title", f"\n  {title}\n\n"))
        for i, (_, label) in enumerate(options):
            if i == state["idx"]:
                lines.append(("class:pointer", "  > "))
                lines.append(("class:selected", f"{label}\n"))
            else:
                lines.append(("", f"    {label}\n"))
        lines.append(("class:hint", "\n  [Up/Down/j/k to move, Enter to select]\n"))
        return lines

    kb = KeyBindings()

    @kb.add("up")
    def _up(event):
        state["idx"] = (state["idx"] - 1) % len(options)

    @kb.add("down")
    def _down(event):
        state["idx"] = (state["idx"] + 1) % len(options)

    @kb.add("k")
    def _k(event):
        state["idx"] = (state["idx"] - 1) % len(options)

    @kb.add("j")
    def _j(event):
        state["idx"] = (state["idx"] + 1) % len(options)

    @kb.add("enter")
    def _enter(event):
        event.app.exit()

    @kb.add("c-c")
    def _ctrlc(event):
        raise KeyboardInterrupt

    layout = Layout(
        Window(content=FormattedTextControl(get_tokens, focusable=True, show_cursor=False))
    )
    style = Style.from_dict({
        'title': 'bold ansicyan',
        'pointer': 'bold ansigreen',
        'selected': 'bold',
        'hint': 'ansigray',
    })
    application = Application(layout=layout, key_bindings=kb, full_screen=False, style=style)
    application.run()
    return options[state["idx"]][0]


def _render_title() -> None:
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
        subtitle="[bold white]v1.0.0 Engine Ready[/]",
        width=100
    )
    console.print(panel)


def _render_instruction(label: str, rules: str, example: str) -> None:
    text = Text.from_markup(f"[bold cyan]Rules   :[/] {rules}\n[bold cyan]Example :[/] {example}")
    panel = Panel(text, title=f"[bold yellow]{label}[/]", border_style="cyan", padding=(0, 2), width=90)
    console.print("\n")
    console.print(panel)


def _ask_input_path() -> Path:
    while True:
        _render_instruction(
            "Input Excel File",
            "Provide the full path to an existing [bold].xlsx[/bold] wrapper. The first sheet will be processed row-by-row.",
            "[green]/Users/you/Documents/orders.xlsx[/green]",
        )
        raw_path = Prompt.ask("  [bold cyan]?[/] Path to input Excel file (.xlsx)").strip()
        input_path = Path(raw_path).expanduser()
        if not input_path.exists():
            console.print("  [bold red][!] File does not exist. Please check the path and try again.[/]")
            continue
        if input_path.suffix.lower() != ".xlsx":
            console.print("  [bold red][!] Invalid format. Only .xlsx files are supported.[/]")
            continue
        return input_path


def _ask_billing_mode() -> BillingMode:
    return BillingMode(ascii_select(
        "Billing Account Mode",
        [
            (BillingMode.CUSTOM.value, "Custom Billing  -- dynamic per-row UPI ID derived from Excel columns (default)"),
            (BillingMode.STATIC.value, "Static Merchant -- identical single UPI ID applied to all rows"),
        ],
        default_index=0,
    ))


def _ask_custom_billing_details() -> tuple[str, str, str]:
    """Returns (vpa_prefix, vpa_suffix, vpa_middle_col_name)."""
    text = Text.from_markup(
        "VPA is built dynamically per row as: [bold cyan]<prefix><column_value><suffix>[/]\n"
        "e.g.  [bold yellow]hello.<InvoiceID>@okaxis[/]"
    )
    panel = Panel(text, title="[bold magenta]Custom Billing Details[/]", border_style="magenta", padding=(0, 2), width=90)
    console.print("\n")
    console.print(panel)

    vpa_prefix = Prompt.ask("  [bold cyan]?[/] VPA Prefix (e.g. hello.)").strip()
    vpa_suffix = Prompt.ask("  [bold cyan]?[/] VPA Suffix (e.g. @okaxis)").strip()

    while True:
        col = Prompt.ask("  [bold cyan]?[/] Excel column name for VPA middle part").strip()
        if col:
            vpa_middle_col = col
            break
        console.print("  [bold red][!] Column name cannot be empty.[/]")

    return vpa_prefix, vpa_suffix, vpa_middle_col


def _ask_static_vpa() -> str:
    while True:
        _render_instruction(
            "Merchant VPA (Static)",
            "Enter the fixed UPI ID to receive all payments in this batch.",
            "[green]merchant@okaxis[/green]",
        )
        value = Prompt.ask("  [bold cyan]?[/] Merchant VPA (UPI ID)").strip()
        if value:
            return value
        console.print("  [bold red][!] Merchant VPA cannot be empty.[/]")


def _ask_static_payee_name() -> str:
    while True:
        _render_instruction(
            "Payee Name",
            "This exact name will be displayed to the user on their banking app during the scan.",
            "[green]Your Brand Name[/green]",
        )
        value = Prompt.ask("  [bold cyan]?[/] Payee Name").strip()
        if value:
            return value
        console.print("  [bold red][!] Payee Name cannot be empty.[/]")


def _ask_note() -> str:
    _render_instruction(
        "Transaction Note",
        "Optional contextual note included in the payment request. Keep it brief.",
        "[green]Payment for order[/green]",
    )
    return Prompt.ask("  [bold cyan]?[/] Transaction Note", default="Payment for order").strip()


def _ask_qr_mode() -> QRMode:
    return QRMode(ascii_select(
        "QR Output Generation Mode",
        [
            (QRMode.EMBED.value, "Embed QR  -- Insert generated QR images directly into Excel cells (recommended)"),
            (QRMode.HYPERLINK.value, "Link QR   -- Save QR images in a folder and create clickable hyperlinks in excel"),
        ],
        default_index=0,
    ))


def _choose_main_menu() -> str:
    return ascii_select(
        "Core System Menu",
        [
            ("start", "Start New QR Generation Batch Run"),
            ("view_errors", "View Diagnostics & Errors from Last Run"),
            ("quit", "Exit System safely"),
        ],
        default_index=0,
    )


def _resolve_session_db(input_path: Path) -> tuple[Path, bool]:
    resumable = find_resumable_session_for_input(input_path)
    if resumable is not None and resumable.exists():
        return resumable, True
    session_id = make_session_id()
    return init_session_db_from_template(session_id), False


def _print_summary(summary: ProcessSummary, db_path: Path) -> None:
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


def _show_last_run_errors(last_session_db: Path | None) -> None:
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


def _run_single_session() -> tuple[Path, ProcessSummary]:
    input_path = _ask_input_path()
    billing_mode = _ask_billing_mode()

    vpa_prefix = vpa_suffix = vpa_middle_col = ""
    vpa = ""

    if billing_mode == BillingMode.CUSTOM:
        vpa_prefix, vpa_suffix, vpa_middle_col = _ask_custom_billing_details()
    else:
        vpa = _ask_static_vpa()

    payee_name = _ask_static_payee_name()
    note = _ask_note()
    mode = _ask_qr_mode()

    session_db, resumed = _resolve_session_db(input_path)
    if resumed:
        console.print(f"\n  [~] Resuming interrupted session from: {session_db}\n")

    logo_path_env = os.getenv("UPI_QR_LOGO_PATH", "").strip()
    logo_path = Path(logo_path_env).expanduser() if logo_path_env else None

    config = ProcessConfig(
        billing_mode=billing_mode,
        vpa=vpa,
        payee_name=payee_name,
        vpa_prefix=vpa_prefix,
        vpa_suffix=vpa_suffix,
        vpa_middle_col_name=vpa_middle_col,
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
            console.print("\n  [bold green][OK] Core system safely shutdown.[/]\n")
            return

        if choice == "view_errors":
            _show_last_run_errors(last_session_db)
            continue

        if choice == "start":
            cleaned = archive_or_delete_completed_sessions()
            if cleaned > 0:
                console.print(f"\n  [bold cyan][~] Log rotation: Cleared {cleaned} completed session archives.[/]\n")

            session_db = None
            try:
                session_db, summary = _run_single_session()
                last_session_db = session_db
                _print_summary(summary, session_db)
            except KeyboardInterrupt:
                if session_db is not None:
                    last_session_db = session_db
                console.print("\n  [bold yellow][!] Run interrupted by operator. Halting safely and returning to main menu.[/]\n")
            except Exception as exc:  # pragma: no cover - defensive guard for unexpected errors.
                console.print(f"\n  [bold red][ERR] Unexpected core exception:[/bold red] {exc}\n")


@app.callback(invoke_without_command=True)
def entrypoint(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _run_interactive()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
