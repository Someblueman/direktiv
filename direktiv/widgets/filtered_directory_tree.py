"""A directory tree widget that can hide dotfiles.

This is a lightweight replacement for textual.widgets.DirectoryTree with
optional filtering for hidden entries (dotfiles).
"""

from pathlib import Path
from typing import Any, Iterable

from textual import on
from textual.widgets import Tree
from textual.widgets.tree import TreeNode


class FilteredDirectoryTree(Tree[Path]):
    """Tree widget for browsing the filesystem with hidden-file filtering."""

    def __init__(self, root_path: Path, show_dotfiles: bool = False, **kwargs: Any) -> None:
        super().__init__(label=str(root_path), data=root_path, **kwargs)
        self.root_path = root_path
        self.show_dotfiles = show_dotfiles
        self.can_focus = True

    def on_mount(self) -> None:  # type: ignore[override]
        self.show_root = False
        self._populate_node(self.root, self.root_path)
        self.root.expand()

    def _iter_children(self, path: Path) -> Iterable[Path]:
        try:
            for child in sorted(path.iterdir(), key=lambda p: (not p.is_dir(), p.name.lower())):
                # Skip hidden entries when show_dotfiles is False
                if not self.show_dotfiles and child.name.startswith('.'):
                    continue
                yield child
        except Exception:
            return

    def _populate_node(self, node: TreeNode[Path], path: Path) -> None:
        # Remove any existing children before repopulating
        try:
            node.remove_children()
        except Exception:
            pass
        for child in self._iter_children(path):
            label = f"📁 {child.name}" if child.is_dir() else child.name
            child_node = node.add(label, data=child)
            if child.is_dir():
                # Defer loading children until expanded
                child_node.allow_expand = True

    @on(Tree.NodeExpanded)
    def on_node_expanded(self, event: Tree.NodeExpanded[Path]) -> None:
        node = event.node
        if node.data and node.data.is_dir():
            # Only populate if this is the first expansion or currently empty
            if not node.children:
                self._populate_node(node, node.data)
