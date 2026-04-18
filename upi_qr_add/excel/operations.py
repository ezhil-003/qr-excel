"""Excel openpyxl manipulations."""

from __future__ import annotations

from pathlib import Path
from openpyxl.worksheet.worksheet import Worksheet
from openpyxl.drawing.image import Image as XLImage
from openpyxl.utils import get_column_letter

from ..core.exceptions import ExcelProcessingError

QR_COLUMN_MIN_WIDTH = 24
QR_IMAGE_SIZE_PX = 120
QR_ROW_MIN_HEIGHT = 96

def setup_qr_column(ws: Worksheet, qr_col: int, header_row: int = 1) -> str:
    """Set the header and adjust the width for the QR code column."""
    try:
        ws.cell(row=header_row, column=qr_col, value="payment_qr")
        qr_col_letter = get_column_letter(qr_col)
        ws.column_dimensions[qr_col_letter].width = max(
            ws.column_dimensions[qr_col_letter].width or 0,
            QR_COLUMN_MIN_WIDTH,
        )
        return qr_col_letter
    except Exception as e:
        raise ExcelProcessingError(f"Failed to setup QR column: {e}")

def embed_qr_image(ws: Worksheet, image_path: Path, row_idx: int, col_letter: str) -> None:
    """Embed the QR image into the specified cell."""
    try:
        target_cell = f"{col_letter}{row_idx}"
        xl_img = XLImage(str(image_path))
        xl_img.width = QR_IMAGE_SIZE_PX
        xl_img.height = QR_IMAGE_SIZE_PX
        ws.add_image(xl_img, target_cell)
        ws.row_dimensions[row_idx].height = max(
            ws.row_dimensions[row_idx].height or 0,
            QR_ROW_MIN_HEIGHT,
        )
    except Exception as e:
        raise ExcelProcessingError(f"Failed to embed QR image at row {row_idx}: {e}")

def add_qr_hyperlink(ws: Worksheet, row_idx: int, col_idx: int, rel_path: str) -> None:
    """Add a hyperlink to an external QR image."""
    try:
        cell = ws.cell(row=row_idx, column=col_idx, value="Open QR")
        cell.hyperlink = rel_path
        cell.style = "Hyperlink"
    except Exception as e:
        raise ExcelProcessingError(f"Failed to add QR hyperlink at row {row_idx}: {e}")
