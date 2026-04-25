"""Typer entrypoint for the UPI QR CLI."""

from __future__ import annotations

import os
import sys
import traceback
from pathlib import Path

import typer

# Support local execution fallback
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
    from upi_qr_add.core.models import ProcessConfig, ProcessSummary, BillingMode
    from upi_qr_add.core.exceptions import UPIQRError
    from upi_qr_add.core.processor import process_workbook
    from upi_qr_add.database.logger import archive_or_delete_completed_sessions, find_latest_session_db, find_resumable_session_for_input, init_session_db_from_template
    from upi_qr_add.utils.paths import make_session_id
    from upi_qr_add import __version__
else:
    from ..core.models import ProcessConfig, ProcessSummary, BillingMode
    from ..core.exceptions import UPIQRError
    from ..core.processor import process_workbook
    from ..database.logger import archive_or_delete_completed_sessions, find_latest_session_db, find_resumable_session_for_input, init_session_db_from_template
    from ..utils.paths import make_session_id
    from .. import __version__

from .prompts import (
    ask_input_path, ask_billing_mode, ask_custom_billing_details, 
    ask_static_vpa, ask_static_payee_name, ask_note, ask_qr_mode, choose_main_menu
)
from .display import console, show_error, render_title, print_summary, show_last_run_errors, print_raw, render_boot_sequence

app = typer.Typer(add_completion=False, no_args_is_help=False)


def _resolve_session_db(input_path: Path) -> tuple[Path, bool]:
    resumable = find_resumable_session_for_input(input_path)
    if resumable is not None and resumable.exists():
        return resumable, True
    session_id = make_session_id()
    return init_session_db_from_template(session_id), False


def _run_single_session() -> tuple[Path, ProcessSummary]:
    input_path = ask_input_path()
    billing_mode = ask_billing_mode()

    vpa_prefix = vpa_suffix = vpa_middle_col = ""
    vpa = ""

    if billing_mode == BillingMode.CUSTOM:
        vpa_prefix, vpa_suffix, vpa_middle_col = ask_custom_billing_details()
    else:
        vpa = ask_static_vpa()

    payee_name = ask_static_payee_name()
    note = ask_note()
    mode = ask_qr_mode()

    session_db, resumed = _resolve_session_db(input_path)
    if resumed:
        print_raw(f"\n  [~] Resuming interrupted session from: {session_db}\n")

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
    render_boot_sequence()
    render_title(__version__)
    last_session_db: Path | None = find_latest_session_db()

    while True:
        choice = choose_main_menu()
        if choice == "quit":
            archive_or_delete_completed_sessions()
            print_raw("\n  [bold green][OK] Core system safely shutdown.[/]\n")
            return

        if choice == "view_errors":
            show_last_run_errors(last_session_db)
            continue

        if choice == "start":
            cleaned = archive_or_delete_completed_sessions()
            if cleaned > 0:
                print_raw(f"\n  [bold cyan][~] Log rotation: Cleared {cleaned} completed session archives.[/]\n")

            session_db = None
            try:
                session_db, summary = _run_single_session()
                last_session_db = session_db
                print_summary(summary, session_db)
            except UPIQRError as core_err:
                show_error(f"Execution Error: {core_err}")
                print_raw("\n  [bold yellow][!] Run aborted due to error above. Returning to main menu.[/]\n")
            except KeyboardInterrupt:
                if session_db is not None:
                    last_session_db = session_db
                print_raw("\n  [bold yellow][!] Run interrupted by operator. Halting safely and returning to main menu.[/]\n")
            except Exception as exc:  # fallback guard for highly unexpected developer errors
                print_raw(f"\n  [bold red][ERR] Unexpected core exception:[/bold red] {exc}\n")
                traceback.print_exc(file=sys.stderr)


@app.callback(invoke_without_command=True)
def entrypoint(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _run_interactive()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
