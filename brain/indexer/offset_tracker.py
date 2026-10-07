"""Incremental byte-offset tracking for append-only transcript ingestion."""

import os
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

class OffsetTracker:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._init_table()

    def _init_table(self):
        sql = """
        CREATE TABLE IF NOT EXISTS ingestion_offsets (
            file_path TEXT PRIMARY KEY,
            mtime REAL NOT NULL,
            file_size INTEGER NOT NULL,
            byte_offset INTEGER NOT NULL,
            updated_at TEXT NOT NULL
        );
        """
        self.conn.execute(sql)
        self.conn.commit()

    def check_file_status(self, file_path: Path) -> Tuple[bool, int]:
        """
        Determines whether file needs processing and returns starting byte offset.
        Returns: (needs_processing: bool, start_offset: int)
        """
        if not file_path.exists():
            return False, 0

        stat = file_path.stat()
        current_mtime = stat.st_mtime
        current_size = stat.st_size

        cursor = self.conn.execute(
            "SELECT mtime, file_size, byte_offset FROM ingestion_offsets WHERE file_path = ?",
            (str(file_path),),
        )
        row = cursor.fetchone()

        if not row:
            # First time seeing this file
            return True, 0

        saved_mtime, saved_size, saved_offset = row

        if current_size > saved_size or current_mtime > saved_mtime:
            # File grew or changed
            # If file was truncated/re-written, start from 0
            if current_size < saved_size:
                return True, 0
            return True, saved_offset

        # File is unchanged
        return False, saved_size

    def commit_offset(self, file_path: Path, new_offset: int):
        stat = file_path.stat()
        sql = """
        INSERT INTO ingestion_offsets (file_path, mtime, file_size, byte_offset, updated_at)
        VALUES (?, ?, ?, ?, datetime('now'))
        ON CONFLICT(file_path) DO UPDATE SET
            mtime = excluded.mtime,
            file_size = excluded.file_size,
            byte_offset = excluded.byte_offset,
            updated_at = excluded.updated_at
        """
        self.conn.execute(sql, (str(file_path), stat.st_mtime, stat.st_size, new_offset))
        self.conn.commit()
