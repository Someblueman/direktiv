"""Main application for direktiv."""

from pathlib import Path
from typing import Any, Optional

from textual import events
from textual.app import App, ComposeResult
from textual.containers import Container, Horizontal
from textual.widgets import Footer, Header

from .database import Database
from .document_manager import DocumentManager
from .widgets.dialogs import (
    CategorySelectDialog,
    InputDialog,
    MessageDialog,
    SimpleFileDialog,
    MultiSelectFileDialog,
)
from .widgets.file_tree import FileTree
from .widgets.viewer import MarkdownViewer


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
        ("a", "add_documents", "Add Documents"),
        ("n", "new_category", "New Category"),
        ("f", "new_folder", "New Folder"),
        (".", "toggle_dotfiles", "Toggle Hidden"),
    ]

    def __init__(self, root_dir: Optional[Path] = None, **kwargs: Any) -> None:
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
        self.doc_manager = DocumentManager(
            self.root_dir, show_dotfiles=self.show_dotfiles
        )
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
                    doc_manager=self.doc_manager,  # Pass the app's doc_manager
                    id="file-tree",
                )
                yield self.file_tree

                self.viewer = MarkdownViewer(id="markdown-viewer")
                yield self.viewer

        yield Footer()

    def on_mount(self) -> None:
        """Called when the app is mounted."""
        self.title = "direktiv"
        self.sub_title = "Personal Markdown Document Manager"
        # Set focus to file tree initially
        if self.file_tree:
            self.file_tree.focus()

    def action_refresh(self) -> None:
        """Refresh the file tree."""
        if self.file_tree:
            self.file_tree.refresh_tree()

    def action_toggle_dotfiles(self) -> None:
        """Toggle visibility of dotfiles."""
        if self.file_tree:
            self.file_tree.toggle_dotfiles()
            # Keep app-level flag in sync for dialogs
            self.show_dotfiles = self.file_tree.show_dotfiles

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
        - a: Add documents (multi-select files or directories)
        - n: Create new category (folder)
        - f: Create new folder (same as 'n')
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

    def action_add_documents(self) -> None:
        """Start worker to add one or more documents or directories."""
        self.run_worker(self._flow_add_documents())

    async def _flow_add_documents(self) -> None:
        """Unified flow: select files and/or directories, then choose category, then add/import."""
        selections = await self.push_screen_wait(
            MultiSelectFileDialog(
                title="Add Documents to Library",
                show_dotfiles=self.show_dotfiles,
            )
        )
        if not selections:
            return

        categories = self.doc_manager.list_categories()
        category = await self.push_screen_wait(
            CategorySelectDialog(
                title="Select Category",
                categories=categories,
                default_category="General",
            )
        )
        if not category:
            return

        total_added = 0
        messages: list[str] = []
        for path in selections:
            if path.is_dir():
                # Import all markdown files recursively from directory into chosen category
                success_count, fail_count, msgs = self.doc_manager.import_directory(
                    path, category, recursive=True
                )
                total_added += success_count
                messages.extend(msgs)
            elif path.is_file():
                success, message, library_path = self.doc_manager.add_document(path, category)
                if success and library_path:
                    self.database.add_document(
                        str(library_path), category=category, original_path=str(path)
                    )
                    total_added += 1
                    messages.append(message)
                else:
                    messages.append(message)

        if self.file_tree:
            self.file_tree.refresh_tree()

        if self.viewer:
            result_text = f"""# Add Results

Added {total_added} document(s) to {category}
"""
            if len(messages) <= 30 and messages:
                result_text += "\n## Details:\n\n"
                for msg in messages:
                    result_text += f"- {msg}\n"
            self.viewer.show_content(result_text, is_markdown=True)

    # Removed separate import flow; unified under add_documents

    async def action_new_folder(self) -> None:
        """Alias for new_category - creates a new folder."""
        self.action_new_category()

    def action_new_category(self) -> None:  # type: ignore[func-returns-value]
        """Start worker to create a new category via dialog."""
        self.run_worker(self._flow_new_category())

    async def _flow_new_category(self) -> None:
        category_name = await self.push_screen_wait(
            InputDialog(
                title="Create New Category",
                prompt="Enter category name:",
                placeholder="e.g., Projects, Research, Notes",
            )
        )
        if not category_name:
            return

        success, message = self.doc_manager.create_category(category_name)
        if success:
            self.database.add_category(category_name)
            if self.file_tree:
                self.file_tree.refresh_tree()
            if self.viewer:
                self.viewer.show_content(
                    f"# Category Created\n\n{message}", is_markdown=True
                )
        else:
            await self.push_screen_wait(MessageDialog("Error", message))


    def on_file_tree_file_selected(self, message: Any) -> None:
        """Handle file selection from file tree."""
        if self.viewer and message.file_path:
            self.viewer.show_file(message.file_path)
            # Update database with library path
            self.database.update_last_opened(str(message.file_path))

            # Ensure document is in database
            if not self.database.get_document_info(str(message.file_path)):
                # Determine category from path
                category = message.file_path.parent.name
                self.database.add_document(str(message.file_path), category=category)
