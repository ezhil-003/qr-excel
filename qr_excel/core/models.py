"""Data models and enums for the UPI QR operation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path


class QRMode(str, Enum):
    EMBED = "embed"
    HYPERLINK = "hyperlink"


class BillingMode(str, Enum):
    STATIC = "static"
    CUSTOM = "custom"


@dataclass(slots=True)
class ProcessConfig:
    # --- Common ---
    note: str = "Payment for order"
    mode: QRMode = QRMode.EMBED
    logo_path: Path | None = None
    db_path: Path = Path("upi_qr_log.db")
    billing_mode: BillingMode = BillingMode.CUSTOM
    amount_col_name: str = "Amount"

    # --- Static billing (single merchant) ---
    vpa: str = ""
    payee_name: str = ""

    # --- Custom billing (per-row UPI ID from Excel column) ---
    vpa_prefix: str = ""
    vpa_suffix: str = ""
    vpa_middle_col_name: str = ""

    def __post_init__(self) -> None:
        if not self.amount_col_name:
            raise ValueError("Amount column header name cannot be empty.")
        if self.billing_mode == BillingMode.STATIC and not self.vpa:
            raise ValueError("Static billing mode requires a non-empty VPA.")
        if self.billing_mode == BillingMode.CUSTOM and not self.vpa_middle_col_name:
            raise ValueError("Custom billing mode requires a VPA middle column name.")


@dataclass(slots=True)
class ProcessSummary:
    total_rows: int
    successful: int
    failed: int
    skipped: int
    output_file: Path
    resumed_from: int | None
    interrupted: bool
    status: str
    session_id: str
    error_message: str | None = None

    @property
    def failed_total(self) -> int:
        return self.failed + self.skipped
