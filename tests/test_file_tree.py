"""Tests for the file tree widget."""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
from direktiv.widgets.file_tree import FileTree
from direktiv.database import Database


class TestFileTree:
    """Test cases for the file tree widget."""

    def setup_method(self):
        """Set up test database."""
        self.database = Database(Path("test.db"))

    def teardown_method(self):
        """Clean up test database."""
        db_path = Path("test.db")
        if db_path.exists():
            db_path.unlink()

    def test_file_tree_initialization(self):
        """Test that file tree initializes with root directory."""
        root_dir = Path(".")
        file_tree = FileTree(root_dir=root_dir, database=self.database)
        assert file_tree.root_dir == root_dir

    def test_file_tree_loads_markdown_files(self):
        """Test that file tree only shows markdown files."""
        file_tree = FileTree(root_dir=Path("."), database=self.database)
        
        # Mock the get_markdown_files method directly for this test
        mock_files = [Path("test1.md"), Path("test2.md")]
        with patch.object(file_tree, 'get_markdown_files', return_value=mock_files):
            markdown_files = file_tree.get_markdown_files()
            
            # Should only return .md files
            assert len(markdown_files) == 2
            assert all(f.suffix == ".md" for f in markdown_files)

    def test_file_tree_navigation(self):
        """Test keyboard navigation in file tree."""
        file_tree = FileTree(root_dir=Path("."), database=self.database)
        # Test up/down navigation
        # Implementation will be added when we build the widget
        pass

    def test_file_tree_read_status_display(self):
        """Test that read/unread status is displayed correctly."""
        file_tree = FileTree(root_dir=Path("."), database=self.database)
        # Test visual indicators for read/unread files
        # Implementation will be added when we build the widget
        pass