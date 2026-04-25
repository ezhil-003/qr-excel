# qr-excel

`qr-excel` is an interactive Python CLI to add dynamic UPI payment QR codes into Excel files for large row counts (2000+).

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

### One-Line Install (macOS / Linux)
The fastest way to install the latest standalone binary:
```bash
curl -sL https://raw.githubusercontent.com/ezhil-003/qr-excel/main/scripts/install.sh | bash
```

### One-Line Install (Windows)
The fastest way to install the latest standalone binary on Windows via PowerShell:
```powershell
irm https://raw.githubusercontent.com/ezhil-003/qr-excel/main/scripts/install.ps1 | iex
```

### Manual Binary Download
Download the standalone executable for your platform from the [GitHub Releases](https://github.com/ezhil-003/qr-excel/releases) page. No Python installation required!

### Developer / Python Install
If you prefer to run it via Python from source:

#### From Project Root (macOS / Linux / Windows)
```bash
pip install -e .
```

Then run:
```bash
qr-excel
```

## Interactive Flow

When you run `qr-excel`, use the arrow-key menu:

1. `Start New Run`
2. `View Last Run Errors`
3. `Quit`

### Working Pattern & Modes

The CLI supports two primary VPA (UPI ID) generation modes:

**1. Custom Billing Account (Dynamic VPA)**
- Ideal for spreadsheets where each row has a different billing account.
- The tool dynamically constructs the VPA for each row by taking a base prefix, appending the value from a specified column in the Excel row, and appending a suffix.
- It also dynamically fetches the Payee Name from another column in the row.
- Example: Prefix `merchant.`, Column `AccountID` (row value `1234`), Suffix `@okbiz` -> `merchant.1234@okbiz`.

**2. Static VPA**
- Uses a unified VPA and Payee Name for the entire spreadsheet.

For each input step, the CLI displays rules + examples before prompting:
- Input Excel path (`.xlsx`)
- Billing Setup (Custom vs Static)
- Transaction Note (default: `Payment for order`)
- QR Output Mode:
  - **Embed**: Embeds the generated image directly in an Excel cell (default and recommended).
  - **Hyperlink**: Saves image files in a subfolder and adds clickable links in Excel.

Output file is auto-created beside input:
`original_filename_with_qr.xlsx`

During processing, an interactive Dot-Highlighter ASCII menu displays progress. Press `Ctrl+C` to interrupt safely and return to the menu. Checkpoints + logs are preserved for resume.

## Runtime Session DB

- A template DB ships with the package at:
  `qr_excel/assets/upi_qr_template.db`
- Runtime DB files are created per session under:
  `~/.qr-excel/sessions/session_<timestamp_pid>.db`
- Completed session DBs are cleared automatically when starting a new run.

## Environment Variables

Optional settings are listed in `.env.example`:

- `UPI_QR_LOGO_PATH`: Custom logo path (default: packaged `assets/upi_logo.png`)

## Default UPI Logo Asset

Default logo path used by the package:

`qr_excel/assets/upi_logo.png`

Replace this file with your official UPI logo anytime, or use `UPI_QR_LOGO_PATH`.

If the logo file is missing or unreadable, QR generation continues without logo overlay and logs a warning.

## Running Tests

```bash
pytest
```
