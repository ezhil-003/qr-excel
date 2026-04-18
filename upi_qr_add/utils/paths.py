"""Shared constants and path resolution logic."""

from __future__ import annotations

import os
from datetime import datetime, timezone
from pathlib import Path


def default_logo_path() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "upi_logo.png"


def template_db_path() -> Path:
    return Path(__file__).resolve().parent.parent / "assets" / "upi_qr_template.db"


def app_runtime_dir() -> Path:
    return Path.home() / ".upi-qr-add"


def app_sessions_dir() -> Path:
    return app_runtime_dir() / "sessions"


def make_session_id() -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    return f"{now}_{os.getpid()}"


def session_db_path(session_id: str) -> Path:
    return app_sessions_dir() / f"session_{session_id}.db"


def output_excel_path(input_file: Path) -> Path:
    return input_file.with_name(f"{input_file.stem}_with_qr.xlsx")


def checkpoint_key(input_file: Path, output_file: Path, sheet_name: str) -> str:
    return f"{input_file.resolve()}::{output_file.resolve()}::{sheet_name}"
