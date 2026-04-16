from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from openpyxl import Workbook, load_workbook
from PIL import Image

from upi_qr_add.core import ProcessConfig, QRMode, process_workbook
from upi_qr_add.qr_generator import create_decorated_qr_image


def create_excel(path: Path, headers: list[str], rows: list[list[object]]) -> None:
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    wb.save(path)


def test_decorated_qr_generation_with_and_without_logo(tmp_path: Path) -> None:
    logo_path = tmp_path / "logo.png"
    Image.new("RGBA", (80, 80), (0, 102, 204, 255)).save(logo_path)

    with_logo = create_decorated_qr_image(
        "upi://pay?pa=a@b&pn=Demo&am=1.00&tr=123&tn=Test&cu=INR",
        logo_path=logo_path,
    )
    assert with_logo.size == (420, 420)
    assert with_logo.mode == "RGB"

    without_logo = create_decorated_qr_image(
        "upi://pay?pa=a@b&pn=Demo&am=2.00&tr=124&tn=Test&cu=INR",
        logo_path=tmp_path / "missing_logo.png",
    )
    assert without_logo.size == (420, 420)


def test_embed_mode_success_and_invalid_rows(tmp_path: Path) -> None:
    input_file = tmp_path / "orders.xlsx"
    create_excel(
        input_file,
        headers=["OrderID", "Amount"],
        rows=[
            [1, 100],
            [2, None],
            [3, "abc"],
            [4, -1],
            [5, 0],
            [6, "49.50"],
        ],
    )
    db_path = tmp_path / "upi_qr_log.db"
    config = ProcessConfig(
        vpa="merchant@okaxis",
        payee_name="Demo Store",
        note="Payment for order",
        mode=QRMode.EMBED,
        db_path=db_path,
    )

    summary = process_workbook(input_file, config)

    assert summary.total_rows == 6
    assert summary.successful == 2
    assert summary.skipped == 4
    assert summary.failed == 0
    assert summary.output_file.exists()

    wb = load_workbook(summary.output_file)
    ws = wb.active
    assert ws.cell(row=1, column=3).value == "payment_qr"
    assert len(ws._images) == 2

    conn = sqlite3.connect(db_path)
    steps = conn.execute("SELECT step, status FROM row_logs").fetchall()
    conn.close()
    assert ("create_qr_with_logo", "success") in steps
    assert ("validate_amount", "failed") in steps


def test_hyperlink_mode_creates_qr_files_and_links(tmp_path: Path) -> None:
    input_file = tmp_path / "sales.xlsx"
    create_excel(
        input_file,
        headers=["Amount"],
        rows=[
            [10],
            [20.5],
        ],
    )
    db_path = tmp_path / "hyper_log.db"
    config = ProcessConfig(
        vpa="merchant@okaxis",
        payee_name="Shop Name",
        mode=QRMode.HYPERLINK,
        db_path=db_path,
    )

    summary = process_workbook(input_file, config)
    assert summary.successful == 2
    assert summary.failed_total == 0

    wb = load_workbook(summary.output_file)
    ws = wb.active
    link_cell_1 = ws.cell(row=2, column=2)
    link_cell_2 = ws.cell(row=3, column=2)
    assert link_cell_1.value == "Open QR"
    assert link_cell_1.hyperlink is not None
    assert link_cell_2.hyperlink is not None

    image_dir = tmp_path / "sales_with_qr_qr_images"
    assert image_dir.exists()
    png_files = list(image_dir.glob("*.png"))
    assert len(png_files) == 2


def test_missing_amount_column_raises_clear_error(tmp_path: Path) -> None:
    input_file = tmp_path / "missing_amount.xlsx"
    create_excel(
        input_file,
        headers=["Total", "OrderID"],
        rows=[[100, 1]],
    )
    config = ProcessConfig(
        vpa="merchant@okaxis",
        payee_name="Demo",
        mode=QRMode.EMBED,
        db_path=tmp_path / "missing_col.db",
    )

    with pytest.raises(ValueError, match='Missing required "Amount" column'):
        process_workbook(input_file, config)


def test_resume_after_interruption_uses_checkpoint(tmp_path: Path) -> None:
    input_file = tmp_path / "resume.xlsx"
    create_excel(
        input_file,
        headers=["Amount"],
        rows=[
            [100],
            [200],
            [300],
        ],
    )
    db_path = tmp_path / "resume_log.db"
    config = ProcessConfig(
        vpa="merchant@okaxis",
        payee_name="Resume Merchant",
        mode=QRMode.EMBED,
        db_path=db_path,
    )

    first_run = process_workbook(input_file, config, stop_after_rows=1)
    assert first_run.interrupted is True
    assert first_run.successful == 1

    second_run = process_workbook(input_file, config)
    assert second_run.interrupted is False
    assert second_run.resumed_from == 2
    assert second_run.successful == 2

    wb = load_workbook(second_run.output_file)
    ws = wb.active
    assert len(ws._images) == 3

    conn = sqlite3.connect(db_path)
    checkpoint = conn.execute(
        "SELECT last_successful_row FROM checkpoints"
    ).fetchone()
    conn.close()
    assert checkpoint is not None
    assert checkpoint[0] == 4
