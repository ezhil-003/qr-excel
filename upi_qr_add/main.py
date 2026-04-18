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
from rich import box
from rich.console import Console
from rich.prompt import Prompt
from rich.table import Table

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

ASCII_BANNER = r"""
/==========================================================================================\
|  01001001 01001110 01001010 01000101 01000011 01010100 01010011 01010101 01000101        |
|  01001001 01010100 01000101 01000001 01001101 01010011 01001001 01010100 01010100        |
|                                                                                          |
|  +================================================================================+     |
|  | ##  ## ####  ##    ##  #####  ####  ####  #####  ##  ## ##  ####  #####       |     |
|  | ##  ## ##  # ##    ## ##   ## ##  # ##  # ##     ##  ## ## ##  #  ##          |     |
|  | ##  ## ####  ##    ## ##   ## ####  ####  #####  ##  ## ## ##     #####       |     |
|  | ##  ## ##    ## ## ## ##   ## ## #  ##    ##      ####  ## ##  #  ##          |     |
|  |  ####  ##     #####   #####  ##  ## ##    #####    ##   ##  ####  #####       |     |
|  +================================================================================+     |
|                                                                                          |
|  [BOOT]   +--[ CORE ]----------------------------------------------------------+        |
|  [INIT]   |  * Payload Engine    : ONLINE                                      |        |
|  [LOAD]   |  * Reflection Probe  : OK                                          |        |
|  [READY]  |  * QR Modules        : EMBED | HYPERLINK                           |        |
|  [SET]    +--------------------------------------------------------------------+        |
|                                                                                          |
\==========================================================================================/
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
        lines.append(("bold", f"  {title}\n"))
        for i, (_, label) in enumerate(options):
            if i == state["idx"]:
                lines.append(("", "  > "))
                lines.append(("bold", f"{label}\n"))
            else:
                lines.append(("", f"    {label}\n"))
        lines.append(("", "\n  [Up/Down to move, Enter to select]\n"))
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
    application = Application(layout=layout, key_bindings=kb, full_screen=False)
    application.run()
    return options[state["idx"]][0]


def _render_title() -> None:
    console.print(ASCII_BANNER)


def _render_instruction(label: str, rules: str, example: str) -> None:
    console.print(f"\n  +-- {label} --+")
    console.print(f"  | Rules   : {rules}")
    console.print(f"  | Example : {example}")
    console.print(f"  +-{'─' * (len(label) + 6)}+\n")


def _ask_input_path() -> Path:
    while True:
        _render_instruction(
            "Input Excel File",
            "Provide an existing .xlsx file path. First sheet will be processed.",
            "/Users/you/Documents/orders.xlsx",
        )
        raw_path = Prompt.ask("  Path to input Excel file (.xlsx)").strip()
        input_path = Path(raw_path).expanduser()
        if not input_path.exists():
            console.print("  [!] File does not exist. Please try again.")
            continue
        if input_path.suffix.lower() != ".xlsx":
            console.print("  [!] Only .xlsx files are supported.")
            continue
        return input_path


def _ask_billing_mode() -> BillingMode:
    console.print()
    value = ascii_select(
        "Billing Account Mode",
        [
            (BillingMode.CUSTOM.value, "Custom Billing  -- per-row UPI ID from Excel columns (default)"),
            (BillingMode.STATIC.value, "Static Merchant -- single UPI ID for all rows"),
        ],
        default_index=0,
    )
    return BillingMode(value)


def _ask_custom_billing_details() -> tuple[str, str, str]:
    """Returns (vpa_prefix, vpa_suffix, vpa_middle_col_name)."""
    console.print("\n  +-- Custom Billing Details --+")
    console.print("  | VPA is built as: <prefix><column_value><suffix>")
    console.print("  | e.g.  hello.<InvoiceID>@okaxis\n")

    vpa_prefix = Prompt.ask("  VPA Prefix (e.g. hello.)").strip()
    vpa_suffix = Prompt.ask("  VPA Suffix (e.g. @okaxis)").strip()

    while True:
        col = Prompt.ask("  Excel column name for VPA middle part").strip()
        if col:
            vpa_middle_col = col
            break
        console.print("  [!] Column name cannot be empty.")

    return vpa_prefix, vpa_suffix, vpa_middle_col


def _ask_static_vpa() -> str:
    while True:
        _render_instruction(
            "Merchant VPA",
            "Non-empty UPI ID in provider format.",
            "merchant@okaxis",
        )
        value = Prompt.ask("  Merchant VPA (UPI ID)").strip()
        if value:
            return value
        console.print("  [!] Merchant VPA cannot be empty.")


def _ask_static_payee_name() -> str:
    while True:
        _render_instruction(
            "Payee Name",
            "Non-empty display name used in UPI payment request.",
            "Ezhil Sivaraj",
        )
        value = Prompt.ask("  Payee Name").strip()
        if value:
            return value
        console.print("  [!] Payee Name cannot be empty.")


def _ask_note() -> str:
    _render_instruction(
        "Transaction Note",
        "Optional free text. Keep it short and clear.",
        "Payment for order",
    )
    return Prompt.ask("  Transaction Note", default="Payment for order").strip()


def _ask_qr_mode() -> QRMode:
    console.print()
    value = ascii_select(
        "QR Output Mode",
        [
            (QRMode.EMBED.value, "Embed QR image directly in Excel cell (recommended)"),
            (QRMode.HYPERLINK.value, "Save QR images in subfolder and insert hyperlink"),
        ],
        default_index=0,
    )
    return QRMode(value)


def _choose_main_menu() -> str:
    console.print()
    return ascii_select(
        "Main Menu",
        [
            ("start", "Start New Run"),
            ("view_errors", "View Last Run Errors"),
            ("quit", "Quit"),
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
    console.print("\n  +-- Run Summary " + "-" * 40 + "+")
    rows = [
        ("Status", summary.status),
        ("Session ID", summary.session_id),
        ("Total rows", str(summary.total_rows)),
        ("Successful", str(summary.successful)),
        ("Failed", str(summary.failed_total)),
        ("Output file", str(summary.output_file)),
    ]
    if summary.resumed_from is not None:
        rows.append(("Resumed from row", str(summary.resumed_from + 1)))
    if summary.error_message:
        rows.append(("Setup Error", summary.error_message))
    rows.append(("Session DB", str(db_path)))
    for key, val in rows:
        console.print(f"  | {key:<20} : {val}")
    console.print("  +" + "-" * 56 + "+\n")


def _show_last_run_errors(last_session_db: Path | None) -> None:
    target_db = last_session_db if last_session_db and last_session_db.exists() else find_latest_session_db()
    if target_db is None:
        console.print("\n  [!] No session logs found.\n")
        return

    with SQLiteLogger(target_db) as logger:
        state = logger.get_session_state()
        failed_rows = logger.get_failed_logs(session_id=str(state["session_id"]))
        session_events = logger.get_session_events()

    console.print(f"\n  +-- Session: {state['session_id']}  Status: {state['status']} --+")
    console.print(f"  | DB: {target_db}\n")

    if failed_rows:
        console.print("  +-- Row-Level Failures " + "-" * 36 + "+")
        header = f"  | {'Timestamp':<26} {'Row':<5} {'Step':<22} {'Error':<20} {'Message'}"
        console.print(header)
        console.print("  |" + "-" * 95)
        for row in failed_rows:
            line = (
                f"  | {str(row['timestamp'] or ''):<26}"
                f" {str(row['row_index'] or ''):<5}"
                f" {str(row['step'] or ''):<22}"
                f" {str(row['error_type'] or ''):<20}"
                f" {str(row['error_message'] or '')}"
            )
            console.print(line)
        console.print("  +" + "-" * 96 + "+\n")
    else:
        console.print("  [OK] No failed row entries in the selected session.\n")

    failed_events = [e for e in session_events if e["status"] == "failed"]
    if failed_events:
        console.print("  +-- Session-Level Errors " + "-" * 34 + "+")
        for event in failed_events:
            console.print(
                f"  | {str(event['timestamp'] or ''):<26}"
                f" {str(event['step'] or ''):<22}"
                f" {str(event['error_type'] or ''):<20}"
                f" {str(event['error_message'] or '')}"
            )
        console.print("  +" + "-" * 96 + "+\n")


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
            console.print("\n  [OK] Session ended.\n")
            return

        if choice == "view_errors":
            _show_last_run_errors(last_session_db)
            continue

        if choice == "start":
            cleaned = archive_or_delete_completed_sessions()
            if cleaned > 0:
                console.print(f"\n  [~] Cleared {cleaned} completed session log file(s).\n")

            session_db = None
            try:
                session_db, summary = _run_single_session()
                last_session_db = session_db
                _print_summary(summary, session_db)
            except KeyboardInterrupt:
                if session_db is not None:
                    last_session_db = session_db
                console.print("\n  [!] Interrupted by user. Returned to main menu.\n")
            except Exception as exc:  # pragma: no cover - defensive guard for unexpected errors.
                console.print(f"\n  [ERR] Unexpected error: {exc}\n")


@app.callback(invoke_without_command=True)
def entrypoint(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _run_interactive()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
