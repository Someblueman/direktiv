"""Tests for database operations."""

import pytest
import sqlite3
import tempfile
from pathlib import Path
from direktiv.database import Database


class TestDatabase:
    """Test cases for database operations."""

    def setup_method(self):
        """Set up test database."""
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = Path(self.temp_db.name)
        self.temp_db.close()
        self.database = Database(self.db_path)

    def teardown_method(self):
        """Clean up test database."""
        if self.db_path.exists():
            self.db_path.unlink()

    def test_database_initialization(self):
        """Test that database initializes and creates tables."""
        assert self.db_path.exists()
        
        # Check that the file_status table exists
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='file_status'"
        )
        result = cursor.fetchone()
        conn.close()
        
        assert result is not None

    def test_mark_file_as_read(self):
        """Test marking a file as read."""
        file_path = "/test/file.md"
        self.database.mark_as_read(file_path)
        
        assert self.database.is_read(file_path) is True

    def test_mark_file_as_unread(self):
        """Test marking a file as unread."""
        file_path = "/test/file.md"
        self.database.mark_as_read(file_path)
        self.database.mark_as_unread(file_path)
        
        assert self.database.is_read(file_path) is False

    def test_get_read_status_default(self):
        """Test that new files default to unread."""
        file_path = "/test/new_file.md"
        assert self.database.is_read(file_path) is False

    def test_get_all_read_files(self):
        """Test getting all read files."""
        files = ["/test/file1.md", "/test/file2.md", "/test/file3.md"]
        
        # Mark first two as read
        self.database.mark_as_read(files[0])
        self.database.mark_as_read(files[1])
        
        read_files = self.database.get_read_files()
        assert len(read_files) == 2
        assert files[0] in read_files
        assert files[1] in read_files
        assert files[2] not in read_files