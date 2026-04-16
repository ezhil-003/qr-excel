# upi-qr-add

`upi-qr-add` is an interactive Python CLI to add dynamic UPI payment QR codes into Excel files for large row counts (2000+).

## Features

- Interactive CLI with `typer` + `rich` prompts.
- Reads `.xlsx` with `openpyxl`.
- Validates the `Amount` column (case-insensitive).
- Adds a `payment_qr` column at the end.
- Generates per-row UPI deep links with unique transaction IDs.
- Builds decorated QR codes with centered UPI logo using `qrcode` + `Pillow`.
- Two QR output modes:
  - Embed image directly in Excel cell (default and recommended).
  - Save image files in a subfolder and add hyperlinks in Excel.
- Live processing progress with `tqdm`.
- SQLite-based structured logging (`upi_qr_log.db`).
- SQLite checkpoint resume support for interrupted runs.

## Installation

From the project root:

```bash
pip install -e .
```

Then run:

```bash
upi-qr-add
```

## Interactive Flow

When you run `upi-qr-add`, it prompts for:

1. Input Excel path (`.xlsx`)
2. Merchant VPA (UPI ID)
3. Payee Name
4. Transaction Note (default: `Payment for order`)
5. QR mode:
   1. Embed QR image in Excel cell (recommended/default)
   2. Save QR images in subfolder + put hyperlink in Excel

Output file is auto-created beside input:

`original_filename_with_qr.xlsx`

## Environment Variables

Optional settings are listed in `.env.example`:

- `UPI_QR_DB_PATH`: SQLite log DB path (default: `upi_qr_log.db`)
- `UPI_QR_LOGO_PATH`: Custom logo path (default: packaged `assets/upi_logo.png`)

## Default UPI Logo Asset

Default logo path used by the package:

`upi_qr_add/assets/upi_logo.png`

Replace this file with your official UPI logo anytime, or use `UPI_QR_LOGO_PATH`.

If the logo file is missing or unreadable, QR generation continues without logo overlay and logs a warning.

## Running Tests

```bash
pytest
```
