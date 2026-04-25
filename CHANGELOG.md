# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
