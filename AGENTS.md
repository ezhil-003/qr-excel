# AGENTS

This repository provides a command‑line tool **upi‑qr‑add** that helps you generate and embed decorated UPI QR codes into Excel spreadsheets.

## Primary Agent

- **CLI Agent** – Powered by **Typer**, this agent parses command‑line arguments, orchestrates the QR code generation using **qrcode** and **Pillow**, and writes the resulting images into the specified Excel rows via **openpyxl**.

## Supporting Agents

- **Progress Agent** – Utilises **tqdm** to display a progress bar while processing large spreadsheets.
- **Logging Agent** – Uses **Rich** for colourful, structured console logs, making it easy to trace the execution flow.
- **Prompt Agent** – Leverages **prompt_toolkit** to provide an interactive, auto‑complete prompt when the CLI is invoked without required arguments.

These agents work together to provide a smooth, interactive experience for users who need to batch‑process UPI QR codes.
