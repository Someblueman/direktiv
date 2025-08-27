"""File tree widget for direktiv."""

import shutil
from pathlib import Path
from typing import List, Optional, Set

from textual import on
from textual.message import Message
from textual.widgets import Tree
from textual.widgets.tree import TreeNode

from ..database import Database


class FileTree(Tree[Path]):
    """A tree widget for browsing markdown files."""

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
        **kwargs
    ) -> None:
        """Initialize the file tree.
        
        Args:
            root_dir: Root directory to browse
            database: Database instance for read status
        """
        super().__init__(
            label=str(root_dir.name),
            data=root_dir,
            **kwargs
        )
        self.root_dir = root_dir
        self.database = database
        self.can_focus = True
        self.border_title = "Files"

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        self.show_root = False
        self._populate_tree()

    def _populate_tree(self) -> None:
        """Populate the tree with markdown files and directories."""
        self._add_directory_contents(self.root, self.root_dir)
        self.root.expand()

    def _add_directory_contents(self, node: TreeNode[Path], directory: Path) -> None:
        """Add contents of a directory to the tree.
        
        Args:
            node: Tree node to add contents to
            directory: Directory to scan
        """
        try:
            # Get all items in directory
            items = sorted(directory.iterdir(), key=lambda x: (x.is_file(), x.name.lower()))
            
            for item in items:
                if item.is_dir():
                    # Add directory node - Textual provides its own expand/collapse indicator
                    dir_node = node.add(item.name, data=item)
                    # Recursively add contents if directory contains markdown files
                    if self._has_markdown_files(item):
                        self._add_directory_contents(dir_node, item)
                elif item.suffix.lower() == '.md':
                    # Add markdown file with read status indicator
                    is_read = self.database.is_read(str(item))
                    status_icon = "✓" if is_read else "●"
                    node.add(f"{status_icon} {item.name}", data=item)
        except PermissionError:
            # Skip directories we can't read
            pass

    def _has_markdown_files(self, directory: Path) -> bool:
        """Check if directory contains markdown files recursively.
        
        Args:
            directory: Directory to check
            
        Returns:
            True if directory contains .md files
        """
        try:
            for item in directory.rglob("*.md"):
                if item.is_file():
                    return True
        except PermissionError:
            pass
        return False

    def get_markdown_files(self) -> List[Path]:
        """Get all markdown files in the root directory.
        
        Returns:
            List of markdown file paths
        """
        markdown_files = []
        try:
            for item in self.root_dir.rglob("*.md"):
                if item.is_file():
                    markdown_files.append(item)
        except PermissionError:
            pass
        return sorted(markdown_files)

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

    def _restore_expanded_state(self, expanded_paths: Set[Path], node: Optional[TreeNode[Path]] = None) -> None:
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
        
        # Rebuild tree
        self.clear()
        self._populate_tree()
        
        # Restore expanded state
        self._restore_expanded_state(expanded_paths)
        
        # Try to restore selection
        if selected_path:
            self._select_path(selected_path)

    def _select_path(self, target_path: Path, node: Optional[TreeNode[Path]] = None) -> bool:
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

    def delete_file(self, file_path: Path) -> bool:
        """Delete a file.
        
        Args:
            file_path: Path to the file to delete
            
        Returns:
            True if deletion was successful
        """
        try:
            file_path.unlink()
            self.refresh_tree()
            return True
        except Exception:
            return False

    def add_file(self, source_path: Path, destination_name: Optional[str] = None) -> bool:
        """Copy a file to the current directory.
        
        Args:
            source_path: Path to source file
            destination_name: Optional destination filename
            
        Returns:
            True if copy was successful
        """
        try:
            if not source_path.exists() or source_path.suffix.lower() != '.md':
                return False
            
            dest_name = destination_name or source_path.name
            dest_path = self.root_dir / dest_name
            
            # Avoid overwriting existing files
            counter = 1
            while dest_path.exists():
                name_part = dest_path.stem
                dest_path = self.root_dir / f"{name_part}_{counter}.md"
                counter += 1
            
            shutil.copy2(source_path, dest_path)
            self.refresh_tree()
            return True
        except Exception:
            return False

    def get_selected_file(self) -> Optional[Path]:
        """Get the currently selected file.
        
        Returns:
            Path to selected file or None
        """
        if self.cursor_node and self.cursor_node.data:
            if self.cursor_node.data.is_file():
                return self.cursor_node.data
        return None

    async def key_space(self) -> None:
        """Handle space key - toggle read status."""
        selected_file = self.get_selected_file()
        if selected_file:
            current_status = self.database.is_read(str(selected_file))
            self.mark_file_read(selected_file, not current_status)

    async def key_delete(self) -> None:
        """Handle delete key - delete selected file."""
        selected_file = self.get_selected_file()
        if selected_file:
            # In a real app, you'd show a confirmation dialog
            self.delete_file(selected_file)