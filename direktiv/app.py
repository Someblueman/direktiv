"""Main application for direktiv."""

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Container
from textual.widgets import Header, Footer
from .widgets.file_tree import FileTree
from .widgets.viewer import MarkdownViewer
from .database import Database
from .document_manager import DocumentManager


class DirektivApp(App[None]):
    """Personal markdown document manager application."""

    CSS = """
    #main-container {
        height: 100%;
        width: 100%;
    }
    
    #panes {
        height: 100%;
        width: 100%;
        layout: horizontal;
    }
    
    #file-tree {
        width: 1fr;
        max-width: 50;
        border: round $primary;
        border-title-align: left;
        margin: 0;
        padding: 0;
    }
    
    #file-tree:focus {
        border: round $accent;
    }
    
    #markdown-viewer {
        width: 2fr;
        border: round $primary;
        border-title-align: left;
        margin: 0;
        margin-left: -1;
        padding: 0;
    }
    
    #markdown-viewer:focus {
        border: round $accent;
    }
    """

    BINDINGS = [
        ("q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("r", "refresh", "Refresh"),
        ("h", "help", "Help"),
        ("ctrl+n", "add_file", "Add File"),
    ]

    def __init__(self, root_dir: Optional[Path] = None, **kwargs) -> None:
        """Initialize the application.

        Args:
            root_dir: Root directory for documents. Defaults to ~/.direktiv/documents
        """
        super().__init__(**kwargs)
        
        # Default to library path
        if root_dir is None:
            root_dir = Path.home() / ".direktiv" / "documents"
            root_dir.mkdir(parents=True, exist_ok=True)
        
        self.root_dir = root_dir.resolve()
        self.database = Database()
        self.doc_manager = DocumentManager(self.root_dir)
        self.file_tree: Optional[FileTree] = None
        self.viewer: Optional[MarkdownViewer] = None
        self.dark = True  # Use dark theme

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        with Container(id="main-container"):
            with Horizontal(id="panes"):
                self.file_tree = FileTree(
                    root_dir=self.root_dir, database=self.database, id="file-tree"
                )
                yield self.file_tree

                self.viewer = MarkdownViewer(id="markdown-viewer")
                yield self.viewer

        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "direktiv"
        self.sub_title = "Personal Markdown Document Manager"

    def action_refresh(self) -> None:
        """Refresh the file tree."""
        if self.file_tree:
            self.file_tree.refresh_tree()

    def action_help(self) -> None:
        """Show help information."""
        help_text = """
        direktiv - Personal Markdown Document Manager
        
        File Status Icons:
        ● Unread document    ✓ Read document
        
        Navigation:
        - Arrow keys: Navigate categories and documents
        - Enter: Open selected document
        - Space: Mark document as read/unread
        - Del: Delete selected document
        - Ctrl+N: Add new document
        
        Global shortcuts:
        - r: Refresh library
        - q/Ctrl+C: Quit
        - h: Show this help
        
        CLI Commands:
        - direktiv add <file>: Add document to library
        - direktiv list: List all documents
        - direktiv new-category: Create category
        """
        if self.viewer:
            self.viewer.show_content(help_text, is_markdown=True)

    def action_add_file(self) -> None:
        """Show add file dialog."""
        if self.file_tree:
            # Show instructions for adding documents
            if self.viewer:
                add_help = """
                Add Documents to Library
                
                To add documents to your library, exit the viewer (press 'q') and use:
                
                ```bash
                # Add a single document
                direktiv add path/to/document.md
                
                # Add to specific category
                direktiv add doc.md --category Work
                
                # Import entire directory
                direktiv import ~/Documents/notes
                ```
                
                Press 'r' to refresh the library after adding documents.
                """
                self.viewer.show_content(add_help, is_markdown=True)

    def on_file_tree_file_selected(self, message) -> None:
        """Handle file selection from file tree."""
        if self.viewer and message.file_path:
            self.viewer.show_file(message.file_path)
            # Update database with library path
            self.database.update_last_opened(str(message.file_path))
            
            # Ensure document is in database
            if not self.database.get_document_info(str(message.file_path)):
                # Determine category from path
                category = message.file_path.parent.name
                self.database.add_document(
                    str(message.file_path),
                    category=category
                )
