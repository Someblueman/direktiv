"""Database operations for direktiv."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import List, Optional


class Database:
    """SQLite database for storing file read status."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize database connection.
        
        Args:
            db_path: Path to database file. If None, uses default location.
        """
        if db_path is None:
            # Store in user's home directory
            db_path = Path.home() / ".direktiv" / "database.db"
            db_path.parent.mkdir(exist_ok=True)
        
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS file_status (
                    file_path TEXT PRIMARY KEY,
                    is_read BOOLEAN DEFAULT FALSE,
                    last_opened TIMESTAMP,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def mark_as_read(self, file_path: str) -> None:
        """Mark a file as read.
        
        Args:
            file_path: Path to the file
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_status 
                (file_path, is_read, last_opened, date_added)
                VALUES (?, TRUE, ?, COALESCE(
                    (SELECT date_added FROM file_status WHERE file_path = ?),
                    CURRENT_TIMESTAMP
                ))
            """, (file_path, datetime.now().isoformat(), file_path))
            conn.commit()

    def mark_as_unread(self, file_path: str) -> None:
        """Mark a file as unread.
        
        Args:
            file_path: Path to the file
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_status 
                (file_path, is_read, date_added)
                VALUES (?, FALSE, COALESCE(
                    (SELECT date_added FROM file_status WHERE file_path = ?),
                    CURRENT_TIMESTAMP
                ))
            """, (file_path, file_path))
            conn.commit()

    def is_read(self, file_path: str) -> bool:
        """Check if a file is marked as read.
        
        Args:
            file_path: Path to the file
            
        Returns:
            True if file is read, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT is_read FROM file_status WHERE file_path = ?",
                (file_path,)
            )
            result = cursor.fetchone()
            return bool(result[0]) if result else False

    def update_last_opened(self, file_path: str) -> None:
        """Update the last opened timestamp for a file.
        
        Args:
            file_path: Path to the file
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO file_status 
                (file_path, is_read, last_opened, date_added)
                VALUES (?, COALESCE(
                    (SELECT is_read FROM file_status WHERE file_path = ?),
                    FALSE
                ), ?, COALESCE(
                    (SELECT date_added FROM file_status WHERE file_path = ?),
                    CURRENT_TIMESTAMP
                ))
            """, (file_path, file_path, datetime.now().isoformat(), file_path))
            conn.commit()

    def get_read_files(self) -> List[str]:
        """Get list of all read files.
        
        Returns:
            List of file paths that are marked as read
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT file_path FROM file_status WHERE is_read = TRUE"
            )
            return [row[0] for row in cursor.fetchall()]

    def get_file_status(self, file_path: str) -> dict:
        """Get complete status information for a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Dictionary with file status information
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT is_read, last_opened, date_added 
                FROM file_status 
                WHERE file_path = ?
            """, (file_path,))
            result = cursor.fetchone()
            
            if result:
                return {
                    "is_read": bool(result[0]),
                    "last_opened": result[1],
                    "date_added": result[2]
                }
            return {
                "is_read": False,
                "last_opened": None,
                "date_added": None
            }