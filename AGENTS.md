# AGENTS

This repository provides a command‑line tool **upi‑qr‑add** that helps you generate and embed decorated UPI QR codes into Excel spreadsheets.

## Primary Agent

- **CLI Agent** – Powered by **Typer**, this agent parses command‑line arguments, requests user configuration interactively (such as choosing between Static VPA and Dynamic Custom Billing VPA), orchestrates the QR code generation using **qrcode** and **Pillow**, and writes the resulting images into the specified Excel rows via **openpyxl**.

## Supporting Agents

- **Progress & UI Agent** – Utilises an internal ASCII-based Dot-Highlighter menu and **tqdm** to display a vibrant, custom interactive progress bar and beautifully formatted final summaries while processing large spreadsheets.
- **Logging Agent** – Uses **Rich** and native console print formatting for colourful, structured console logs, and pairs with SQLite to persistently trace execution flow and log row-level errors for resume capabilities.
- **Prompt Agent** – Leverages **prompt_toolkit** to provide an interactive, auto‑complete prompt handling arrow-key navigation menus when the CLI is invoked.

These agents work together to provide a smooth, interactive experience for users who need to batch‑process UPI QR codes.
