"""Main application for direktiv."""

from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Container
from textual.widgets import Header, Footer
from textual import events

from .widgets.file_tree import FileTree
from .widgets.viewer import MarkdownViewer
from .widgets.dialogs import (
    InputDialog,
    SimpleFileDialog,
    CategorySelectDialog,
    MessageDialog
)
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
        ("?", "help", "Help"),
        ("a", "add_document", "Add Document"),
        ("i", "import_documents", "Import"),
        ("n", "new_category", "New Category"),
        (".", "toggle_dotfiles", "Toggle Hidden"),
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
        self.show_dotfiles = False  # Default to not showing dotfiles
        self.doc_manager = DocumentManager(self.root_dir, show_dotfiles=self.show_dotfiles)
        self.file_tree: Optional[FileTree] = None
        self.viewer: Optional[MarkdownViewer] = None
        self.dark = True  # Use dark theme

    def compose(self) -> ComposeResult:
        """Compose the application layout."""
        yield Header()

        with Container(id="main-container"):
            with Horizontal(id="panes"):
                self.file_tree = FileTree(
                    root_dir=self.root_dir, 
                    database=self.database, 
                    show_dotfiles=self.show_dotfiles,
                    id="file-tree"
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

    def action_toggle_dotfiles(self) -> None:
        """Toggle visibility of dotfiles."""
        if self.file_tree:
            self.file_tree.toggle_dotfiles()
    
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
        
        Global shortcuts:
        - a: Add document to library
        - i: Import documents from directory
        - n: Create new category
        - r: Refresh library
        - .: Toggle hidden directories
        - ?: Show this help
        - q/Ctrl+C: Quit
        
        CLI Commands:
        - direktiv add <file>: Add document to library
        - direktiv import <dir>: Import directory
        - direktiv list: List all documents
        - direktiv new-category: Create category
        """
        if self.viewer:
            self.viewer.show_content(help_text, is_markdown=True)

    async def action_add_document(self) -> None:
        """Show dialog to add a document to library."""
        # First, get the file path
        file_path = await self.push_screen(
            SimpleFileDialog(
                title="Add Document to Library",
                select_directory=False
            )
        )
        
        if not file_path:
            return
        
        # Get list of categories
        categories = self.doc_manager.list_categories()
        
        # Show category selection dialog
        category = await self.push_screen(
            CategorySelectDialog(
                title="Select Category",
                categories=categories,
                default_category="General"
            )
        )
        
        if not category:
            return
        
        # Add the document
        success, message, library_path = self.doc_manager.add_document(
            file_path, category
        )
        
        if success and library_path:
            # Add to database
            self.database.add_document(
                str(library_path),
                category=category,
                original_path=str(file_path)
            )
            
            # Refresh the file tree
            if self.file_tree:
                self.file_tree.refresh_tree()
            
            # Show success message
            if self.viewer:
                self.viewer.show_content(
                    f"# Document Added\n\n{message}",
                    is_markdown=True
                )
        else:
            # Show error message
            await self.push_screen(
                MessageDialog(
                    "Error",
                    message
                )
            )
    
    async def action_import_documents(self) -> None:
        """Show dialog to import documents from a directory."""
        # Get directory path
        dir_path = await self.push_screen(
            SimpleFileDialog(
                title="Import Documents from Directory",
                select_directory=True
            )
        )
        
        if not dir_path:
            return
        
        # Get list of categories
        categories = self.doc_manager.list_categories()
        categories.append("[Use subdirectories as categories]")
        
        # Show category selection dialog
        category = await self.push_screen(
            CategorySelectDialog(
                title="Import to Category",
                categories=categories,
                default_category="[Use subdirectories as categories]"
            )
        )
        
        if not category:
            return
        
        # Handle special case for subdirectory categorization
        if category == "[Use subdirectories as categories]":
            category = None
        
        # Import documents
        success_count, fail_count, messages = self.doc_manager.import_directory(
            dir_path, category, recursive=True
        )
        
        # Update database for imported files
        for doc in self.doc_manager.list_documents():
            if not self.database.get_document_info(doc['path']):
                self.database.add_document(
                    doc['path'],
                    category=doc['category']
                )
        
        # Refresh the file tree
        if self.file_tree:
            self.file_tree.refresh_tree()
        
        # Show results
        if self.viewer:
            result_text = f"""# Import Results

Imported **{success_count}** document(s) from {dir_path}
"""
            if fail_count > 0:
                result_text += f"\nFailed to import **{fail_count}** document(s)\n"
            
            if len(messages) <= 20:
                result_text += "\n## Details:\n\n"
                for msg in messages:
                    result_text += f"- {msg}\n"
            
            self.viewer.show_content(result_text, is_markdown=True)
    
    async def action_new_category(self) -> None:
        """Show dialog to create a new category."""
        # Get category name
        category_name = await self.push_screen(
            InputDialog(
                title="Create New Category",
                prompt="Enter category name:",
                placeholder="e.g., Projects, Research, Notes"
            )
        )
        
        if not category_name:
            return
        
        # Create the category
        success, message = self.doc_manager.create_category(category_name)
        
        if success:
            # Add to database
            self.database.add_category(category_name)
            
            # Refresh the file tree
            if self.file_tree:
                self.file_tree.refresh_tree()
            
            # Show success message
            if self.viewer:
                self.viewer.show_content(
                    f"# Category Created\n\n{message}",
                    is_markdown=True
                )
        else:
            # Show error message
            await self.push_screen(
                MessageDialog(
                    "Error",
                    message
                )
            )

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
