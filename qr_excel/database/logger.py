"""SQLite-backed session logging, checkpoint tracking, and session lifecycle management."""

from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
import shutil

from ..utils.paths import app_sessions_dir, session_db_path, template_db_path


FINAL_STATUSES = {"completed", "completed_with_errors", "setup_failed"}


class SQLiteLogger:
    def __init__(
        self,
        db_path: str | Path,
        *,
        session_id: str | None = None,
    ) -> None:
        try:
            self.db_path = Path(db_path).expanduser().resolve()
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self._conn = sqlite3.connect(self.db_path, timeout=10)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA busy_timeout=5000")
            self._conn.row_factory = sqlite3.Row
        except sqlite3.Error as e:
            raise RuntimeError(f"Failed to connect to session database at {self.db_path}: {e}") from e
        except OSError as e:
            raise RuntimeError(f"Failed to create session directory for {self.db_path}: {e}") from e

        self._init_schema()
        self.session_id = self._ensure_session_state(session_id)

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
            CREATE TABLE IF NOT EXISTS session_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
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
        self._conn.execute(
            """
            CREATE TABLE IF NOT EXISTS session_state (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                session_id TEXT NOT NULL,
                status TEXT NOT NULL,
                input_file TEXT,
                output_file TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )
        self._conn.commit()

    def _ensure_session_state(self, session_id: str | None) -> str:
        row = self._conn.execute(
            """
            SELECT session_id, status, input_file, output_file
            FROM session_state
            WHERE id = 1
            """
        ).fetchone()

        if row is not None:
            existing_session_id = str(row["session_id"])
            if session_id and session_id != existing_session_id:
                self._conn.execute(
                    """
                    UPDATE session_state
                    SET session_id = ?, updated_at = ?
                    WHERE id = 1
                    """,
                    (session_id, self._now()),
                )
                self._conn.commit()
                return session_id
            return existing_session_id

        final_session_id = session_id or self.db_path.stem
        self._conn.execute(
            """
            INSERT INTO session_state (
                id, session_id, status, input_file, output_file, updated_at
            )
            VALUES (1, ?, 'running', NULL, NULL, ?)
            """,
            (final_session_id, self._now()),
        )
        self._conn.commit()
        return final_session_id

    @staticmethod
    def _now() -> str:
        return datetime.now(timezone.utc).isoformat()

    def set_session_state(
        self,
        *,
        status: str,
        input_file: str | Path | None = None,
        output_file: str | Path | None = None,
    ) -> None:
        row = self._conn.execute(
            """
            SELECT input_file, output_file
            FROM session_state
            WHERE id = 1
            """
        ).fetchone()
        if row is None:
            existing_input = None
            existing_output = None
        else:
            existing_input = row["input_file"]
            existing_output = row["output_file"]

        self._conn.execute(
            """
            UPDATE session_state
            SET status = ?, input_file = ?, output_file = ?, updated_at = ?
            WHERE id = 1
            """,
            (
                status,
                str(input_file) if input_file is not None else existing_input,
                str(output_file) if output_file is not None else existing_output,
                self._now(),
            ),
        )
        self._conn.commit()

    def get_session_state(self) -> sqlite3.Row:
        row = self._conn.execute(
            "SELECT session_id, status, input_file, output_file, updated_at FROM session_state WHERE id = 1"
        ).fetchone()
        if row is None:
            raise RuntimeError("Session state is not initialized.")
        return row

    def log_session_event(
        self,
        *,
        step: str,
        status: str,
        error_type: str | None = None,
        error_message: str | None = None,
    ) -> None:
        self._conn.execute(
            """
            INSERT INTO session_events (
                timestamp, step, status, error_type, error_message
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (self._now(), step, status, error_type, error_message),
        )
        self._conn.commit()

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
        # Intentionally not committing here — rows are batched and flushed
        # by update_checkpoint() or an explicit flush() call.

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

    def get_failed_logs(
        self,
        *,
        session_id: str | None = None,
        limit: int | None = None,
    ) -> list[sqlite3.Row]:
        if session_id is not None and session_id != self.session_id:
            return []

        query = """
            SELECT timestamp, row_index, amount, txn_id, step, status, error_type, error_message
            FROM row_logs
            WHERE status = 'failed'
            ORDER BY id ASC
        """
        params: tuple[int, ...] | tuple[()] = ()
        if limit is not None:
            query += " LIMIT ?"
            params = (limit,)

        rows = self._conn.execute(query, params).fetchall()
        return list(rows)

    def get_session_events(self) -> list[sqlite3.Row]:
        rows = self._conn.execute(
            """
            SELECT timestamp, step, status, error_type, error_message
            FROM session_events
            ORDER BY id ASC
            """
        ).fetchall()
        return list(rows)

    def clear_session(self, *, session_id: str | None = None) -> None:
        if session_id is not None and session_id != self.session_id:
            return

        self._conn.execute("DELETE FROM row_logs")
        self._conn.execute("DELETE FROM summary_logs")
        self._conn.execute("DELETE FROM checkpoints")
        self._conn.execute("DELETE FROM session_events")
        self._conn.execute(
            """
            UPDATE session_state
            SET status = 'cleared', input_file = NULL, output_file = NULL, updated_at = ?
            WHERE id = 1
            """,
            (self._now(),),
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

    def flush(self) -> None:
        """Commit any buffered writes (e.g. batched row_logs) to disk."""
        self._conn.commit()

    def close(self) -> None:
        try:
            self._conn.commit()  # flush any pending buffered writes
        except sqlite3.Error:
            pass  # best-effort; don't mask the original error
        self._conn.close()

    def __enter__(self) -> "SQLiteLogger":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:  # type: ignore[override]
        try:
            if exc_type is None:
                self._conn.commit()
            self._conn.close()
        except sqlite3.Error:
            # If already handling an exception, don't mask it.
            # If no original exception, the sqlite error will propagate naturally.
            try:
                self._conn.close()
            except sqlite3.Error:
                pass
            if exc_type is None:
                raise


def init_session_db_from_template(
    session_id: str,
    *,
    sessions_dir: Path | None = None,
    template_db: Path | None = None,
) -> Path:
    target_dir = sessions_dir or app_sessions_dir()
    target_dir.mkdir(parents=True, exist_ok=True)

    source_template = template_db or template_db_path()
    target_db = (
        session_db_path(session_id)
        if sessions_dir is None
        else (target_dir / f"session_{session_id}.db")
    )

    if source_template.exists():
        shutil.copy2(source_template, target_db)
    else:
        import warnings
        warnings.warn(
            f"Session template DB not found at '{source_template}'. "
            "Creating empty session database.",
            stacklevel=2,
        )
        target_db.touch()

    with SQLiteLogger(target_db, session_id=session_id) as logger:
        logger.set_session_state(status="running")
        logger.log_session_event(step="session_initialized", status="success")
    return target_db


def session_db_files(*, sessions_dir: Path | None = None) -> list[Path]:
    target_dir = sessions_dir or app_sessions_dir()
    if not target_dir.exists():
        return []
    return sorted(target_dir.glob("session_*.db"))


def _read_session_state(db_path: Path) -> sqlite3.Row | None:
    try:
        with sqlite3.connect(db_path) as conn:
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT session_id, status, input_file, output_file, updated_at FROM session_state WHERE id = 1"
            ).fetchone()
            return row
    except sqlite3.Error as e:
        import warnings
        warnings.warn(f"Failed to read session state from {db_path}: {e}")
        return None


def archive_or_delete_completed_sessions(*, sessions_dir: Path | None = None) -> int:
    deleted = 0
    for db_file in session_db_files(sessions_dir=sessions_dir):
        row = _read_session_state(db_file)
        if row is None:
            continue
        if row["status"] in FINAL_STATUSES:
            db_file.unlink(missing_ok=True)
            deleted += 1
    return deleted


def find_latest_session_db(*, sessions_dir: Path | None = None) -> Path | None:
    files = session_db_files(sessions_dir=sessions_dir)
    if not files:
        return None
    return max(files, key=lambda path: path.stat().st_mtime)


def find_resumable_session_for_input(
    input_file: Path,
    *,
    sessions_dir: Path | None = None,
) -> Path | None:
    input_resolved = str(input_file.expanduser().resolve())
    interrupted_candidates: list[tuple[Path, str]] = []

    for db_file in session_db_files(sessions_dir=sessions_dir):
        row = _read_session_state(db_file)
        if row is None:
            continue
        status = str(row["status"])
        recorded_input = row["input_file"]
        updated_at = str(row["updated_at"])
        if status == "interrupted" and recorded_input == input_resolved:
            interrupted_candidates.append((db_file, updated_at))

    if not interrupted_candidates:
        return None
    interrupted_candidates.sort(key=lambda item: item[1], reverse=True)
    return interrupted_candidates[0][0]
