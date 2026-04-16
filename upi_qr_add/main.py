from __future__ import annotations

import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

if __package__ in (None, ""):
    import sys

    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from upi_qr_add.core import ProcessConfig, QRMode, process_workbook
else:
    from .core import ProcessConfig, QRMode, process_workbook

app = typer.Typer(add_completion=False, no_args_is_help=False)
console = Console()


def _ask_input_path() -> Path:
    while True:
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
    console.print("\n[bold]QR Mode[/bold]")
    console.print("1. Embed QR image directly in Excel cell [green](recommended)[/green]")
    console.print("2. Save QR images in a subfolder and add hyperlink in the cell")
    selected = Prompt.ask("Choose mode", choices=["1", "2"], default="1")
    return QRMode.EMBED if selected == "1" else QRMode.HYPERLINK


def _run_interactive() -> None:
    console.print(
        Panel.fit(
            "[bold cyan]upi-qr-add[/bold cyan]\nAdd dynamic UPI payment QR codes to Excel rows.",
            border_style="cyan",
        )
    )
    input_path = _ask_input_path()
    vpa = Prompt.ask("Merchant VPA (UPI ID, e.g. merchant@okaxis)").strip()
    payee_name = Prompt.ask("Payee Name").strip()
    note = Prompt.ask("Transaction Note", default="Payment for order").strip()
    mode = _ask_mode()

    logo_path_env = os.getenv("UPI_QR_LOGO_PATH", "").strip()
    logo_path = Path(logo_path_env).expanduser() if logo_path_env else None
    db_path = Path(os.getenv("UPI_QR_DB_PATH", "upi_qr_log.db")).expanduser()

    if not vpa:
        raise typer.BadParameter("Merchant VPA cannot be empty.")
    if not payee_name:
        raise typer.BadParameter("Payee Name cannot be empty.")

    config = ProcessConfig(
        vpa=vpa,
        payee_name=payee_name,
        note=note,
        mode=mode,
        logo_path=logo_path,
        db_path=db_path,
    )

    try:
        summary = process_workbook(input_path, config)
    except Exception as exc:
        console.print(f"[red]Error:[/red] {exc}")
        raise typer.Exit(code=1) from exc

    failed_total = summary.failed_total
    table = Table(title="Run Summary", show_header=False, box=None)
    table.add_row("Total rows", str(summary.total_rows))
    table.add_row("Successful", str(summary.successful))
    table.add_row("Failed", str(failed_total))
    table.add_row("Output file", str(summary.output_file))
    if summary.resumed_from is not None:
        table.add_row("Resumed from row", str(summary.resumed_from + 1))
    if summary.interrupted:
        table.add_row("Status", "Interrupted (checkpoint saved)")

    console.print()
    console.print(table)
    console.print(f"\nStructured log DB: [bold]{db_path.resolve()}[/bold]")


@app.callback(invoke_without_command=True)
def entrypoint(ctx: typer.Context) -> None:
    if ctx.invoked_subcommand is None:
        _run_interactive()


def main() -> None:
    app()


if __name__ == "__main__":
    main()
