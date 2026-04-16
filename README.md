# upi-qr-add

`upi-qr-add` is an interactive Python CLI to add dynamic UPI payment QR codes into Excel files for large row counts (2000+).

## Features

- Interactive CLI with `typer` + `rich` prompts.
- Arrow-key main menu navigation using `prompt_toolkit`.
- Reads `.xlsx` with `openpyxl`.
- Validates the `Amount` column (case-insensitive).
- Adds a `payment_qr` column at the end.
- Generates per-row UPI deep links with unique transaction IDs.
- Builds decorated QR codes with centered UPI logo using `qrcode` + `Pillow`.
- Two QR output modes:
  - Embed image directly in Excel cell (default and recommended).
  - Save image files in a subfolder and add hyperlinks in Excel.
- Live processing progress with `tqdm`.
- Session-isolated SQLite structured logging (one DB per run session).
- SQLite checkpoint resume support for interrupted runs (`Ctrl+C`).
- Main-menu error viewer for row-level and session-level failures.

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

When you run `upi-qr-add`, use the arrow-key menu:

1. `Start New Run`
2. `View Last Run Errors`
3. `Quit`

For each input step, the CLI displays rules + example before prompting:

- Input Excel path (`.xlsx`)
- Merchant VPA (UPI ID)
- Payee Name
- Transaction Note (default: `Payment for order`)
- QR mode (embed/hyperlink)

Output file is auto-created beside input:

`original_filename_with_qr.xlsx`

During processing, press `Ctrl+C` to interrupt safely and return to menu. Checkpoint + logs are preserved for resume.

## Runtime Session DB

- A template DB ships with the package at:
  `upi_qr_add/assets/upi_qr_template.db`
- Runtime DB files are created per session under:
  `~/.upi-qr-add/sessions/session_<timestamp_pid>.db`
- Completed session DBs are cleared automatically when starting a new run.

## Environment Variables

Optional settings are listed in `.env.example`:

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
