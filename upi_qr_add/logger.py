from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path


class SQLiteLogger:
    def __init__(self, db_path: str | Path = "upi_qr_log.db") -> None:
        self.db_path = Path(db_path).expanduser().resolve()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_schema()

    def _init_schema(self) -> None:
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS row_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                row_index INTEGER,
                amount REAL,
                txn_id TEXT,
                step TEXT NOT NULL,
                status TEXT NOT NULL,
                error_type TEXT,
                error_message TEXT
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS summary_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                total_rows INTEGER NOT NULL,
                successful_rows INTEGER NOT NULL,
                failed_rows INTEGER NOT NULL,
                skipped_rows INTEGER NOT NULL,
                output_file TEXT NOT NULL
            )
            """
        )
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS checkpoints (
                checkpoint_key TEXT PRIMARY KEY,
                last_successful_row INTEGER NOT NULL,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def log_step(
        self,
        *,
        row_index: int | None,
        amount: float | None,
        txn_id: str | None,
        step: str,
        status: str,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO row_logs (
                timestamp, row_index, amount, txn_id, step, status, error_type, error_message
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                self._now(),
                row_index,
                amount,
                txn_id,
                step,
                status,
                error_type,
                error_message,
            ),
        )
        self._conn.commit()

    def log_summary(
        self,
        *,
        total_rows: int,
        successful_rows: int,
        failed_rows: int,
        skipped_rows: int,
        output_file: str | Path,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO summary_logs (
                timestamp, total_rows, successful_rows, failed_rows, skipped_rows, output_file
            )
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                self._now(),
                total_rows,
                successful_rows,
                failed_rows,
                skipped_rows,
                str(output_file),
            ),
        )
        self._conn.commit()

    def get_checkpoint(self, key: str) -> int:
        row = self._conn.execute(
            "SELECT last_successful_row FROM checkpoints WHERE checkpoint_key = ?",
            (key,),
        ).fetchone()
        if row is None:
            return 1
        return int(row["last_successful_row"])

    def update_checkpoint(self, key: str, last_successful_row: int) -> None:
        self._conn.execute(
            """
            INSERT INTO checkpoints (checkpoint_key, last_successful_row, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(checkpoint_key) DO UPDATE SET
                last_successful_row = excluded.last_successful_row,
                updated_at = excluded.updated_at
            """,
            (key, last_successful_row, self._now()),
        )
        self._conn.commit()

    def reset_checkpoint(self, key: str) -> None:
        self._conn.execute("DELETE FROM checkpoints WHERE checkpoint_key = ?", (key,))
        self._conn.commit()

    def close(self) -> None:
        self._conn.close()

    def __enter__(self) -> "SQLiteLogger":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore[override]
        self.close()
