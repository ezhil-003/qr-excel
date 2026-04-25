import sqlite3
from pathlib import Path
import pytest
from qr_excel.database.logger import (
    SQLiteLogger,
    archive_or_delete_completed_sessions,
    init_session_db_from_template,
    find_resumable_session_for_input
)
from qr_excel.utils.paths import make_session_id

def test_session_isolation(tmp_path: Path):
    """Verify that each new session gets a unique DB and doesn't leak data."""
    input_file = tmp_path / "data.xlsx"
    input_file.touch()
    
    # 1. Start session A
    sid_a = make_session_id()
    db_a = init_session_db_from_template(sid_a, sessions_dir=tmp_path)
    with SQLiteLogger(db_a, session_id=sid_a) as logger:
        logger.log_step(row_index=1, amount=10.0, txn_id="txn_a", step="test", status="success")
        logger.set_session_state(status="completed")
    
    # 2. Verify session A is NOT resumable
    assert find_resumable_session_for_input(input_file, sessions_dir=tmp_path) is None
    
    # 3. Start session B for same input
    sid_b = make_session_id()
    db_b = init_session_db_from_template(sid_b, sessions_dir=tmp_path)
    assert db_a != db_b
    
    with SQLiteLogger(db_b, session_id=sid_b) as logger:
        # DB should be fresh (empty row_logs)
        rows = logger._conn.execute("SELECT * FROM row_logs").fetchall()
        assert len(rows) == 0
        logger.log_step(row_index=1, amount=20.0, txn_id="txn_b", step="test", status="success")

def test_session_resume_isolation(tmp_path: Path):
    """Verify that only 'interrupted' sessions are resumable."""
    input_file = tmp_path / "resume_data.xlsx"
    input_file.touch()
    
    # 1. Create an interrupted session
    sid_interrupted = "sid_int"
    db_int = init_session_db_from_template(sid_interrupted, sessions_dir=tmp_path)
    with SQLiteLogger(db_int, session_id=sid_interrupted) as logger:
        logger.set_session_state(status="interrupted", input_file=input_file)
        logger.update_checkpoint("run_1", 5)
    
    # 2. Find and resume
    resumable = find_resumable_session_for_input(input_file, sessions_dir=tmp_path)
    assert resumable == db_int
    
    with SQLiteLogger(resumable) as logger:
        assert logger.get_checkpoint("run_1") == 5

def test_cleanup_removes_only_completed(tmp_path: Path):
    """Verify that archive_or_delete_completed_sessions wipes the right files."""
    db1 = init_session_db_from_template("s1", sessions_dir=tmp_path)
    db2 = init_session_db_from_template("s2", sessions_dir=tmp_path)
    
    with SQLiteLogger(db1) as logger:
        logger.set_session_state(status="completed")
    with SQLiteLogger(db2) as logger:
        logger.set_session_state(status="interrupted")
        
    deleted = archive_or_delete_completed_sessions(sessions_dir=tmp_path)
    assert deleted == 1
    assert not db1.exists()
    assert db2.exists()
