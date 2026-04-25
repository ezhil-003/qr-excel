# CLAUDE.md - qr-excel Context

## Project Overview
`qr-excel` is an interactive CLI tool designed to batch-process Excel files and add decorated UPI QR codes to each row. It supports embedding images directly in cells and provides robust session management with SQLite-based checkpointing and error logging.

## Core Technology Stack
- **CLI Framework**: `typer` for command layout.
- **Interactivity**: `prompt_toolkit` for arrow-key menus, ASCII Dot-Highlighter inputs, and interactive configuration.
- **Excel Handling**: `openpyxl` for reading/writing `.xlsx` files and embedding images.
- **QR Generation**: `qrcode` for engine and `Pillow` for image decoration (overlays, resizing).
- **Session/Logging**: `sqlite3` for persistent session logs and error tracking.

## Common Commands

### Setup & Development
```bash
# Install in editable mode
pip install -e .

# Install dependencies only
pip install -r requirements.txt
```

### Execution
```bash
# Run the interactive CLI
qr-excel

# Alternative execution
python run.py
```

### Testing
```bash
# Run all tests
pytest

# Run tests with output
pytest -s
```

## Project Structure
- `qr_excel/`: Main package directory.
  - `cli/`: CLI application logic and UI components.
    - `app.py`: Main Typer application and menu orchestration.
    - `ascii_ui.py`: Custom ASCII rendering logic.
  - `core/`: Business logic and models.
    - `processor.py`: Excel processing orchestration.
    - `models.py`: Data models and validation.
  - `excel/`: Spreadsheet operations and parsing.
  - `qr/`: QR code generation and styling.
  - `utils/`: Path manipulation and miscellaneous helpers.
  - `assets/`: Static icons and SQLite template.
- `tests/`: Pytest suite.
- `requirements.txt`: Flat list of dependencies with versions.
- `pyproject.toml`: Modern Python build metadata and script entry points.

## Coding Style & Guidelines
- **Type Hints**: Use type hints for all functions (`def func(a: int) -> str:`).
- **Error Handling**: Wrap processing loops in try-except; log detailed errors to the session DB via the logging module.
- **UI Consistency**: The application relies on custom ASCII UI styles (Dot-Highlighter menus, ASCII summary text). Avoid full-blown `rich` Panel/Table layouts for standard summaries for an aesthetic ASCII feel.
- **Domain Logic**: Account for both **Static VPA** and **Custom Billing** modes (dynamic VPA construction per row).
- **Concurrency**: The tool is primarily single-threaded to ensure `openpyxl` stability during image embedding.
- **Assets**: Always refer to assets using absolute paths derived in `utils/paths.py` to ensure package portability.
- **Interruption**: Gracefully handle `SIGINT` (Ctrl+C) via Typer/prompt_toolkit to ensure the session DB is closed and user progress can be resumed.
