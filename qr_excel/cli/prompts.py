"""User interaction workflows and prompts."""

from __future__ import annotations

import re
from pathlib import Path

from rich.prompt import Prompt

from .ascii_ui import ascii_select
from .display import console, render_instruction, render_custom_billing_header
from ..core.models import BillingMode, QRMode

_VPA_PATTERN = re.compile(r"^[a-zA-Z0-9._-]+@[a-zA-Z0-9]+$")


def ask_input_path() -> Path:
    while True:
        render_instruction(
            "Input Excel File",
            "Provide the full path to an existing [bold].xlsx[/bold] wrapper. The first sheet will be processed row-by-row.",
            "[green]/Users/you/Documents/orders.xlsx[/green]",
        )
        raw_path = Prompt.ask("  [bold cyan]?[/] Path to input Excel file (.xlsx)").strip()
        if not raw_path:
            console.print("  [bold red][!] Path cannot be empty.[/]")
            continue

        try:
            input_path = Path(raw_path).expanduser().resolve()
        except RuntimeError:
            # Fallback if home directory cannot be determined
            input_path = Path(raw_path).resolve()
        if not input_path.exists():
            console.print("  [bold red][!] File does not exist. Please check the path and try again.[/]")
            continue
        if input_path.suffix.lower() != ".xlsx":
            console.print("  [bold red][!] Invalid format. Only .xlsx files are supported.[/]")
            continue
        return input_path


def ask_amount_column_name() -> str:
    while True:
        render_instruction(
            "Amount Column Header",
            "Type the exact text of the Excel column header containing the payment amounts.",
            "[green]Amount[/green] or [green]Balance_Amount[/green]",
        )
        col = Prompt.ask("  [bold cyan]?[/] Amount Column Header").strip()
        if col:
            return col
        console.print("  [bold red][!] Header name cannot be empty.[/]")


def ask_billing_mode() -> BillingMode:
    return BillingMode(ascii_select(
        "Billing Account Mode",
        [
            (BillingMode.CUSTOM.value, "Custom Billing  -- dynamic per-row UPI ID derived from Excel columns (default)"),
            (BillingMode.STATIC.value, "Static Merchant -- identical single UPI ID applied to all rows"),
        ],
        default_index=0,
    ))


def ask_custom_billing_details() -> tuple[str, str, str]:
    render_custom_billing_header()
    vpa_prefix = Prompt.ask("  [bold cyan]?[/] VPA Prefix (e.g. hello.)").strip()
    vpa_suffix = Prompt.ask("  [bold cyan]?[/] VPA Suffix (e.g. @okaxis)").strip()

    while True:
        col = Prompt.ask("  [bold cyan]?[/] Excel column name for VPA middle part").strip()
        if col:
            return vpa_prefix, vpa_suffix, col
        console.print("  [bold red][!] Column name cannot be empty.[/]")


def ask_static_vpa() -> str:
    while True:
        render_instruction(
            "Merchant VPA (Static)",
            "Enter the fixed UPI ID to receive all payments in this batch.  Format: [bold]localpart@handle[/bold]",
            "[green]merchant@okaxis[/green]",
        )
        value = Prompt.ask("  [bold cyan]?[/] Merchant VPA (UPI ID)").strip()
        if not value:
            console.print("  [bold red][!] Merchant VPA cannot be empty.[/]")
            continue
        if not _VPA_PATTERN.match(value):
            console.print("  [bold red][!] Invalid VPA format. Expected format: localpart@handle (e.g. merchant@okaxis)[/]")
            continue
        return value


def ask_static_payee_name() -> str:
    while True:
        render_instruction(
            "Payee Name",
            "This exact name will be displayed to the user on their banking app during the scan.",
            "[green]Your Brand Name[/green]",
        )
        value = Prompt.ask("  [bold cyan]?[/] Payee Name").strip()
        if value:
            return value
        console.print("  [bold red][!] Payee Name cannot be empty.[/]")


def ask_note() -> str:
    render_instruction(
        "Transaction Note",
        "Optional contextual note included in the payment request. Keep it brief.",
        "[green]Payment for order[/green]",
    )
    return Prompt.ask("  [bold cyan]?[/] Transaction Note", default="Payment for order").strip()


def ask_qr_mode() -> QRMode:
    return QRMode(ascii_select(
        "QR Output Generation Mode",
        [
            (QRMode.EMBED.value, "Embed QR  -- Insert generated QR images directly into Excel cells (recommended)"),
            (QRMode.HYPERLINK.value, "Link QR   -- Save QR images in a folder and create clickable hyperlinks in excel"),
        ],
        default_index=0,
    ))


def choose_main_menu() -> str:
    return ascii_select(
        "Core System Menu",
        [
            ("start", "Start New QR Generation Batch Run"),
            ("view_errors", "View Diagnostics & Errors from Last Run"),
            ("quit", "Exit System safely"),
        ],
        default_index=0,
    )
