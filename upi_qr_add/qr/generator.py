"""QR code image generation with optional centered logo overlay."""

from __future__ import annotations

import warnings
from pathlib import Path

import qrcode
from PIL import Image

from ..utils.paths import default_logo_path


def create_decorated_qr_image(
    upi_url: str,
    *,
    logo_path: str | Path | None = None,
    qr_size: int = 420,
    logo_ratio: float = 0.22,
) -> Image.Image:
    """
    Generate a UPI QR image with centered logo overlay.

    Uses ERROR_CORRECT_H so the QR remains scannable after logo placement.
    If the logo is missing or unreadable, returns plain QR and emits a warning.
    """

    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=4,
    )
    qr.add_data(upi_url)
    qr.make(fit=True)

    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGBA")
    qr_img = qr_img.resize((qr_size, qr_size), Image.Resampling.LANCZOS)

    selected_logo = Path(logo_path) if logo_path is not None else default_logo_path()
    if not selected_logo.exists():
        warnings.warn(
            f"UPI logo not found at '{selected_logo}'. Generating QR without logo.",
            stacklevel=2,
        )
        return qr_img.convert("RGB")

    try:
        logo = Image.open(selected_logo).convert("RGBA")
    except OSError as exc:
        warnings.warn(
            f"Could not load UPI logo from '{selected_logo}': {exc}. "
            "Generating QR without logo.",
            stacklevel=2,
        )
        return qr_img.convert("RGB")

    logo_size = max(1, int(qr_size * logo_ratio))
    logo = logo.resize((logo_size, logo_size), Image.Resampling.LANCZOS)

    offset = ((qr_img.width - logo.width) // 2, (qr_img.height - logo.height) // 2)
    qr_img.paste(logo, offset, logo)
    return qr_img.convert("RGB")
