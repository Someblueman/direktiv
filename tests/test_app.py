"""Tests for the main direktiv application."""

import pytest
from pathlib import Path
from direktiv.app import DirektivApp


class TestDirektivApp:
    """Test cases for the main application."""

    def test_app_initialization(self):
        """Test that the app initializes correctly."""
        test_root = Path(".")
        app = DirektivApp(root_dir=test_root)
        assert app.root_dir == test_root.resolve()

    def test_app_has_required_widgets(self):
        """Test that the app has file tree and viewer widgets."""
        app = DirektivApp(root_dir=Path("."))
        # These will fail until we implement the widgets
        assert hasattr(app, 'file_tree')
        assert hasattr(app, 'viewer')

    def test_app_layout_proportions(self):
        """Test that the layout has correct proportions."""
        app = DirektivApp(root_dir=Path("."))
        # Test will verify left pane is ~30% and right pane is ~70%
        # Implementation details will be added when we build the layout
        pass