from __future__ import annotations

from pathlib import Path
from typing import Any
from urllib.parse import quote, urlencode

from openpyxl.worksheet.worksheet import Worksheet


def normalize_header(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().casefold()


def find_header_index(ws: Worksheet, header_name: str) -> int | None:
    target = header_name.strip().casefold()
    for col in range(1, ws.max_column + 1):
        if normalize_header(ws.cell(row=1, column=col).value) == target:
            return col
    return None


def parse_amount(value: Any) -> float | None:
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, (int, float)):
        return float(value)

    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    return None


def build_upi_deep_link(
    *,
    vpa: str,
    payee_name: str,
    amount: float,
    txn_id: str,
    note: str,
) -> str:
    query = urlencode(
        {
            "pa": vpa,
            "pn": payee_name,
            "am": f"{amount:.2f}",
            "tr": txn_id,
            "tn": note,
            "cu": "INR",
        },
        quote_via=quote,
    )
    return f"upi://pay?{query}"


def default_logo_path() -> Path:
    return Path(__file__).resolve().parent / "assets" / "upi_logo.png"


def output_excel_path(input_file: Path) -> Path:
    return input_file.with_name(f"{input_file.stem}_with_qr.xlsx")


def checkpoint_key(input_file: Path, output_file: Path, sheet_name: str) -> str:
    return f"{input_file.resolve()}::{output_file.resolve()}::{sheet_name}"
