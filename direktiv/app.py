"""Main application for direktiv."""

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.widgets import Header, Footer
from .widgets.file_tree import FileTree
from .widgets.viewer import MarkdownViewer
from .database import Database


class DirektivApp(App[None]):
    """Terminal markdown reader application."""
    
    CSS = """
    FileTree {
        width: 30%;
    }
    
    MarkdownViewer {
        width: 70%;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("h", "help", "Help"),
        ("ctrl+n", "add_file", "Add File"),
    ]

    def __init__(self, root_dir: Path, **kwargs) -> None:
        """Initialize the application.
        
        Args:
            root_dir: Root directory to browse markdown files
        """
        super().__init__(**kwargs)
        self.root_dir = root_dir.resolve()
        self.database = Database()
        self.file_tree: Optional[FileTree] = None
        self.viewer: Optional[MarkdownViewer] = None
        self.dark = True  # Use dark theme

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()
        
        with Horizontal():
            self.file_tree = FileTree(
                root_dir=self.root_dir,
                database=self.database
            )
            yield self.file_tree
            
            self.viewer = MarkdownViewer()
            yield self.viewer
            
        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = f"direktiv - {self.root_dir}"
        self.sub_title = "Terminal Markdown Reader"

    def action_refresh(self) -> None:
        """Refresh the file tree."""
        if self.file_tree:
            self.file_tree.refresh_tree()

    def action_help(self) -> None:
        """Show help information."""
        help_text = """
        direktiv - Terminal Markdown Reader
        
        File Status Icons:
        ● Unread file    ✓ Read file    🗂️ Directory
        
        Navigation:
        - Arrow keys: Navigate file tree
        - Enter: Open selected file
        - Space: Mark file as read/unread
        - Del: Delete selected file
        - Ctrl+N: Add new file
        
        Global shortcuts:
        - r: Refresh file tree
        - q/Ctrl+C: Quit
        - h: Show this help
        """
        if self.viewer:
            self.viewer.show_content(help_text, is_markdown=False)

    def action_add_file(self) -> None:
        """Show add file dialog."""
        if self.file_tree:
            # For now, show a message that the feature is available
            if self.viewer:
                add_help = """
                Add File Feature
                
                To add a file, you can use one of these methods:
                
                1. Copy a markdown file to the current directory manually
                2. Create a new .md file in the directory
                3. Use the file tree's add functionality (future enhancement)
                
                Press 'r' to refresh the file tree after adding files manually.
                """
                self.viewer.show_content(add_help, is_markdown=True)

    def on_file_tree_file_selected(self, message) -> None:
        """Handle file selection from file tree."""
        if self.viewer and message.file_path:
            self.viewer.show_file(message.file_path)
            # Mark file as opened (not necessarily read)
            self.database.update_last_opened(str(message.file_path))