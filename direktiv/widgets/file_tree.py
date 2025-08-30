"""File tree widget for direktiv."""

import shutil
from pathlib import Path
from typing import Any, List, Optional, Set

from textual import events, on
from textual.message import Message
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from ..database import Database
from ..document_manager import DocumentManager


class FileTree(Tree[Path]):
    """A tree widget for browsing documents organized by category."""

    class FileSelected(Message):
        """Message sent when a file is selected."""

        def __init__(self, file_path: Path) -> None:
            """Initialize the message.

            Args:
                file_path: Path to the selected file
            """
            super().__init__()
            self.file_path = file_path

    def __init__(
        self,
        root_dir: Path,
        database: Database,
        show_dotfiles: bool = False,
        doc_manager: Optional[DocumentManager] = None,
        **kwargs: Any,
    ) -> None:
        """Initialize the file tree.

        Args:
            root_dir: Root directory (library path)
            database: Database instance for read status
            show_dotfiles: Whether to show dotfiles (hidden directories)
            doc_manager: Optional DocumentManager instance to use (creates new one if not provided)
        """
        super().__init__(label="Library", data=root_dir, **kwargs)
        self.root_dir = root_dir
        self.database = database
        self.show_dotfiles = show_dotfiles
        # Use provided doc_manager or create a new one
        self.doc_manager = (
            doc_manager
            if doc_manager
            else DocumentManager(root_dir, show_dotfiles=show_dotfiles)
        )
        self.can_focus = True
        self.border_title = "Documents"

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        self.show_root = False
        self._populate_tree()

    def _populate_tree(self) -> None:
        """Populate the tree with categories and documents."""
        self._add_categories_and_documents(self.root)
        self.root.expand()

    def _add_categories_and_documents(self, node: TreeNode[Path]) -> None:
        """Add categories and their documents to the tree.

        Args:
            node: Root tree node
        """
        categories = self.doc_manager.list_categories()

        # Add categories as top-level nodes
        for category in categories:
            category_path = self.root_dir / category
            if category_path.exists():
                # Add category node
                cat_node = node.add(f"📁 {category}", data=category_path)

                # Add documents in this category
                documents = self.doc_manager.list_documents(category)
                for doc in documents:
                    doc_path = Path(doc["path"])
                    if doc_path.exists():
                        # Get read status from database
                        is_read = self.database.is_read(doc["path"])
                        status_icon = "✓" if is_read else "●"
                        doc_node = cat_node.add(
                            f"{status_icon} {doc['name']}", data=doc_path
                        )

                # Expand category if it has documents
                if documents:
                    cat_node.expand()

    def _has_documents(self, category: str) -> bool:
        """Check if category contains documents.

        Args:
            category: Category name

        Returns:
            True if category has documents
        """
        documents = self.doc_manager.list_documents(category)
        return len(documents) > 0

    def get_all_documents(self) -> List[Path]:
        """Get all documents in the library.

        Returns:
            List of document paths
        """
        all_docs = self.doc_manager.list_documents()
        return [Path(doc["path"]) for doc in all_docs if Path(doc["path"]).exists()]

    @on(Tree.NodeSelected)
    def on_node_selected(self, event: Tree.NodeSelected[Path]) -> None:
        """Handle node selection.

        Args:
            event: Node selection event
        """
        if event.node.data and event.node.data.is_file():
            # Post message that file was selected
            self.post_message(self.FileSelected(event.node.data))

    def _get_expanded_paths(self, node: Optional[TreeNode[Path]] = None) -> Set[Path]:
        """Get all expanded directory paths.

        Args:
            node: Starting node (defaults to root)

        Returns:
            Set of expanded directory paths
        """
        if node is None:
            node = self.root

        expanded_paths = set()

        if node.is_expanded and node.data and node.data.is_dir():
            expanded_paths.add(node.data)

        for child in node.children:
            expanded_paths.update(self._get_expanded_paths(child))

        return expanded_paths

    def _restore_expanded_state(
        self, expanded_paths: Set[Path], node: Optional[TreeNode[Path]] = None
    ) -> None:
        """Restore expanded state for directories.

        Args:
            expanded_paths: Set of paths that should be expanded
            node: Starting node (defaults to root)
        """
        if node is None:
            node = self.root

        if node.data and node.data in expanded_paths:
            node.expand()

        for child in node.children:
            self._restore_expanded_state(expanded_paths, child)

    def refresh_tree(self) -> None:
        """Refresh the tree contents while preserving expanded state."""
        # Save expanded state
        expanded_paths = self._get_expanded_paths()

        # Remember current selection
        selected_path = None
        if self.cursor_node and self.cursor_node.data:
            selected_path = self.cursor_node.data

        # Sync database with current documents
        self._sync_database()

        # Rebuild tree
        self.clear()
        self._populate_tree()

        # Restore expanded state
        self._restore_expanded_state(expanded_paths)

        # Try to restore selection
        if selected_path:
            self._select_path(selected_path)

        # Force the widget to refresh its display
        self.refresh()

    def _sync_database(self) -> None:
        """Sync database with current documents in library."""
        all_docs = self.doc_manager.list_documents()
        for doc in all_docs:
            if not self.database.get_document_info(doc["path"]):
                # Add new document to database
                self.database.add_document(doc["path"], category=doc["category"])

    def _select_path(
        self, target_path: Path, node: Optional[TreeNode[Path]] = None
    ) -> bool:
        """Try to select a specific path in the tree.

        Args:
            target_path: Path to select
            node: Starting node (defaults to root)

        Returns:
            True if path was found and selected
        """
        if node is None:
            node = self.root

        if node.data == target_path:
            # Use select_node method instead of setting cursor_node directly
            self.select_node(node)
            return True

        for child in node.children:
            if self._select_path(target_path, child):
                return True

        return False

    def mark_file_read(self, file_path: Path, is_read: bool = True) -> None:
        """Mark a file as read/unread and update display.

        Args:
            file_path: Path to the file
            is_read: True to mark as read, False for unread
        """
        if is_read:
            self.database.mark_as_read(str(file_path))
        else:
            self.database.mark_as_unread(str(file_path))

        # Refresh tree to update status indicators
        self.refresh_tree()

    def delete_document(self, document_path: Path) -> bool:
        """Delete a document from the library.

        Args:
            document_path: Path to the document to delete

        Returns:
            True if deletion was successful
        """
        success, _ = self.doc_manager.delete_document(document_path)
        if success:
            # Remove from database
            self.database.delete_document(str(document_path))
            self.refresh_tree()
        return success

    def add_document(self, source_path: Path, category: str = "General") -> bool:
        """Add a document to the library.

        Args:
            source_path: Path to source document
            category: Category to add to

        Returns:
            True if successful
        """
        success, _, library_path = self.doc_manager.add_document(source_path, category)
        if success and library_path:
            # Add to database
            self.database.add_document(
                str(library_path), category=category, original_path=str(source_path)
            )
            self.refresh_tree()
        return success

    def get_selected_document(self) -> Optional[Path]:
        """Get the currently selected document.

        Returns:
            Path to selected document or None
        """
        if self.cursor_node and self.cursor_node.data:
            data = self.cursor_node.data
            if data.is_file() and data.suffix.lower() == ".md":
                return data
        return None

    def on_key(self, event: events.Key) -> None:
        """Handle key events for file tree specific actions."""
        if event.key == "space":
            """Handle space key - toggle read status."""
            selected_doc = self.get_selected_document()
            if selected_doc:
                current_status = self.database.is_read(str(selected_doc))
                self.mark_file_read(selected_doc, not current_status)
                event.prevent_default()  # Consume this event
                return
        elif event.key == "delete":
            """Handle delete key - delete selected document."""
            selected_doc = self.get_selected_document()
            if selected_doc:
                # In a real app, you'd show a confirmation dialog
                self.delete_document(selected_doc)
                event.prevent_default()  # Consume this event
                return
        
        # For all other keys, explicitly do NOT prevent default
        # This allows them to bubble up to the app level
        # DO NOT call event.prevent_default() or event.stop() here

    def toggle_dotfiles(self) -> None:
        """Toggle visibility of dotfiles."""
        self.show_dotfiles = not self.show_dotfiles
        self.doc_manager.show_dotfiles = self.show_dotfiles
        self.refresh_tree()
        # Update border title to show status
        if self.show_dotfiles:
            self.border_title = "Documents (showing hidden)"
        else:
            self.border_title = "Documents"

    def create_folder(self, folder_name: str) -> bool:
        """Create a new folder (category) in the library.

        Args:
            folder_name: Name of the folder to create

        Returns:
            True if successful
        """
        success, message = self.doc_manager.create_category(folder_name)
        if success:
            self.refresh_tree()
        return success
