# CLAUDE.md - upi-qr-add Context

## Project Overview
`upi-qr-add` is an interactive CLI tool designed to batch-process Excel files and add decorated UPI QR codes to each row. It supports embedding images directly in cells and provides robust session management with SQLite-based checkpointing and error logging.

## Core Technology Stack
- **CLI Framework**: `typer` for command layout and `rich` for UI formatting.
- **Interactivity**: `prompt_toolkit` for arrow-key menus and interactive inputs.
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
upi-qr-add

# Alternative execution
python -m upi_qr_add.main
```

### Testing
```bash
# Run all tests
pytest

# Run tests with output
pytest -s
```

## Project Structure
- `upi_qr_add/`: Main package directory.
  - `main.py`: CLI entry point, menu logic, and Typer app definition.
  - `core.py`: Excel processing orchestration and row iteration.
  - `qr_generator.py`: Specific logic for UPI deep links and Pillow-based QR styling.
  - `logger.py`: SQLite session database management and rich logging.
  - `utils.py`: Path manipulation and miscellaneous helpers.
  - `assets/`: Static icons and SQLite template.
- `tests/`: Pytest suite.
- `requirements.txt`: Flat list of dependencies with versions.
- `pyproject.toml`: Modern Python build metadata and script entry points.

## Coding Style & Guidelines
- **Type Hints**: Use type hints for all functions (`def func(a: int) -> str:`).
- **Error Handling**: Wrap processing loops in try-except; log detailed errors to the session DB via `logger.py`.
- **UI Consistency**: Use `rich` for all console output (tables, panels, colors).
- **Concurrency**: The tool is primarily single-threaded to ensure `openpyxl` stability during image embedding.
- **Assets**: Always refer to assets using absolute paths derived in `utils.py` or `main.py` to ensure package portability.
- **Interruption**: Gracefully handle `SIGINT` (Ctrl+C) via Typer/prompt_toolkit to ensure the session DB is closed and user progress can be resumed.
