# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-04-26

### Added
- **Rebranding**: Project officially renamed to `qr-excel` (formerly `upi-qr-add`).
- **Functional Boot UI**: The technical startup sequence now correctly displays progress for environment scan and module loading in the background.

### Changed
- **Major Refactor**: Structural overhaul of the package. Renamed the core package directory from `upi_qr_add` to `qr_excel`.
- **Package Metadata**: Updated `pyproject.toml`, installers (`install.sh`, `install.ps1`), and CI/CD workflows to reflect the new naming.
- **Resource Management**: Improved handling of temporary files during QR code generation using `tempfile`, preventing accumulation of orphaned image files.

### Fixed
- **Resource Leaks**: Resolved issue where temporary QR images were not being properly cleaned up in some failure modes.
- **Test Regressions**: Updated the test suite to match the new package structure and fixed regressions caused by the rebranding.

## [0.2.3] - 2026-04-25

### Added
- **Fancy Booting UI**: New technical startup sequence with a real-time progress bar and percentage display.
- **Booting Steps**: Visual feedback for environment scan, engine initialization, and module loading.

### Improved
- **ASCII Logo Redesign**: Fixed rendering glitches and improved terminal compatibility using solid block characters.
- **UI Layout**: Optimized panel widths and descriptions for standard 80-column terminal displays.

### Changed
- **Code Splitting**: Decoupled UI data constants from rendering logic for better maintainability.

## [0.2.2] - 2026-04-25

### Fixed
- Adjusted QR code image anchoring to correctly align within the target column (prevent overlapping data).

## [0.2.0] - 2026-04-18

### Fixed
- Adjusted QR code image anchoring to correctly align within the target column (prevent overlapping data).

### Added
- **Multi-Platform Binary Support**: Standalone executables for Linux (amd64), macOS (Universal), and Windows (amd64) via PyInstaller.
- **Automated Releases**: GitHub Actions workflow to auto-build and upload binaries to GitHub Releases on tag push.
- **One-Line Installer**: New bash script for quick installation on macOS and Linux.
- **Package Manager Staging**: Initial setup for Homebrew and Winget distribution.
- **Portable Path Resolution**: Enhanced logic to handle asset loading in standalone binary environments.

## [0.1.1] - 2026-04-18

### Changed
- **Project Structure**: Major refactor into sub-packages (`cli`, `core`, `database`, `excel`, `qr`, `utils`) for better modularity.
- **CLI Entry Point**: Updated script entry point to `upi_qr_add.cli.app:app`.
- **Requirements**: Cleaned up `requirements.txt`.

## [0.1.0] - 2026-04-18

### Added
- **Custom Billing Mode**: Support for dynamic VPA generation based on Excel column values.
- **ASCII UI**: New interactive Vite-like dot-highlighter menu for a premium terminal experience.
- **Excel QR Embedding**: Support for embedding generated QR codes directly into Excel spreadsheet cells.
- **Session Logging**: SQLite-backed session logging for checkpoint/resume and diagnostics.
- **Error Diagnostics**: Built-in error viewer for row-level and session-level failures.
- **Installation**: Support for Windows installation via `winget`.

### Initial
- **Base Functionality**: core UPI QR code generation and basic Excel processing.
