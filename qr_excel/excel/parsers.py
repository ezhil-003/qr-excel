"""Excel cell parsing and header detection."""

from __future__ import annotations

import re
from typing import Any

from openpyxl.worksheet.worksheet import Worksheet


def normalize_header(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip().casefold()


def canonical_header(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "", normalize_header(value))


def find_header_index(ws: Worksheet, header_name: str, *, row: int = 1) -> int | None:
    target = header_name.strip().casefold()
    for col in range(1, ws.max_column + 1):
        if normalize_header(ws.cell(row=row, column=col).value) == target:
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
        cleaned = (
            value.strip()
            .replace(",", "")
            .replace("\u20b9", "")   # ₹ symbol
            .replace("Rs.", "")
            .replace("Rs", "")
            .replace("INR", "")
            .strip()
        )
        if not cleaned:
            return None
        try:
            return float(cleaned)
        except ValueError:
            return None

    return None
