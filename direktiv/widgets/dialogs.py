"""Dialog widgets for direktiv TUI."""

import os
from pathlib import Path
from typing import List, Optional

from textual import on, events
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, ScrollableContainer, Vertical
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Label,
    ListItem,
    ListView,
    Static,
    Tree,
)
from textual.widgets.tree import TreeNode
from .filtered_directory_tree import FilteredDirectoryTree


class InputDialog(ModalScreen[Optional[str]]):
    """Modal dialog for text input."""

    CSS = """
    InputDialog {
        align: center middle;
    }
    
    #dialog-container {
        width: 60;
        height: 11;
        border: thick $background 50%;
        background: $surface;
        padding: 1 2;
    }
    
    #dialog-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $text;
    }
    
    #dialog-prompt {
        margin-bottom: 1;
        color: $text-muted;
    }
    
    #dialog-input {
        width: 100%;
        margin-bottom: 1;
    }
    
    #button-container {
        align: center middle;
        height: 3;
        margin-top: 1;
    }
    
    Button {
        width: 10;
        margin: 0 1;
    }
    """

    def __init__(
        self,
        title: str,
        prompt: str,
        default_value: str = "",
        placeholder: str = "",
        name: Optional[str] = None,
    ):
        """Initialize input dialog.

        Args:
            title: Dialog title
            prompt: Prompt text
            default_value: Default input value
            placeholder: Input placeholder
            name: Screen name
        """
        super().__init__(name=name)
        self.title_text = title
        self.prompt_text = prompt
        self.default_value = default_value
        self.placeholder = placeholder

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Container(id="dialog-container"):
            yield Label(self.title_text, id="dialog-title")
            yield Label(self.prompt_text, id="dialog-prompt")
            yield Input(
                value=self.default_value,
                placeholder=self.placeholder,
                id="dialog-input",
            )
            with Horizontal(id="button-container"):
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Focus input on mount."""
        self.query_one("#dialog-input", Input).focus()

    @on(Button.Pressed, "#ok")
    def on_ok(self) -> None:
        """Handle OK button."""
        value = self.query_one("#dialog-input", Input).value.strip()
        self.dismiss(value if value else None)

    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        """Handle Cancel button."""
        self.dismiss(None)

    @on(Input.Submitted)
    def on_input_submitted(self) -> None:
        """Handle Enter key in input."""
        value = self.query_one("#dialog-input", Input).value.strip()
        self.dismiss(value if value else None)

    def key_escape(self) -> None:
        """Handle ESC key."""
        self.dismiss(None)


class SimpleFileDialog(ModalScreen[Optional[Path]]):
    """Simple file/directory selection dialog."""

    CSS = """
    SimpleFileDialog {
        align: center middle;
    }
    
    #file-container {
        width: 80;
        height: 30;
        border: thick $background 50%;
        background: $surface;
        padding: 1;
    }
    
    #file-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $text;
        height: 1;
    }
    
    #instructions {
        margin-bottom: 1;
        color: $text-muted;
        height: 2;
    }
    
    #path-display {
        background: $boost;
        padding: 0 1;
        margin-bottom: 1;
        height: 1;
        color: $text;
    }
    
    #file-tree {
        height: 1fr;
        border: solid $primary;
        background: $background;
        margin-bottom: 1;
    }
    
    #button-container {
        align: center middle;
        height: 3;
    }
    
    Button {
        width: 10;
        margin: 0 1;
    }
    """

    def __init__(
        self,
        title: str = "Select File",
        start_path: Optional[Path] = None,
        select_directory: bool = False,
        show_dotfiles: bool = False,
        name: Optional[str] = None,
    ):
        """Initialize file dialog.

        Args:
            title: Dialog title
            start_path: Starting directory
            select_directory: If True, select directories instead of files
            name: Screen name
        """
        super().__init__(name=name)
        self.title_text = title
        self.start_path = Path(start_path) if start_path else Path.home()
        self.select_directory = select_directory
        self.show_dotfiles = show_dotfiles
        self.selected_path: Optional[Path] = None

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Container(id="file-container"):
            yield Label(self.title_text, id="file-title")

            if self.select_directory:
                yield Label(
                    "Navigate and select a directory, then click Select.",
                    id="instructions",
                )
            else:
                yield Label(
                    "Navigate and select a markdown file (.md), then click Select.",
                    id="instructions",
                )

            yield Static("No selection", id="path-display")

            yield FilteredDirectoryTree(
                self.start_path, show_dotfiles=self.show_dotfiles, id="file-tree"
            )

            with Horizontal(id="button-container"):
                yield Button("Select", variant="primary", id="select", disabled=True)
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Initialize on mount."""
        tree = self.query_one(Tree)
        tree.focus()

    @on(Tree.NodeSelected)
    def on_tree_selected(self, event: Tree.NodeSelected[Path]) -> None:
        """Handle selection in the tree based on mode."""
        if not event.node or not event.node.data:
            return
        path = event.node.data
        if self.select_directory and path.is_dir():
            self.selected_path = path
        elif not self.select_directory and path.is_file():
            self.selected_path = path
        else:
            # Invalid selection for current mode
            self.selected_path = None

        if self.selected_path:
            self.query_one("#path-display", Static).update(
                f"Selected: {self.selected_path.name}"
            )
            self.query_one("#select", Button).disabled = False
        else:
            self.query_one("#path-display", Static).update("No selection")
            self.query_one("#select", Button).disabled = True

    @on(Button.Pressed, "#select")
    def on_select(self) -> None:
        """Handle Select button."""
        if self.selected_path:
            # Additional validation for markdown files
            if not self.select_directory and self.selected_path.suffix.lower() != ".md":
                self.query_one("#path-display", Static).update(
                    "ERROR: Please select a markdown file (.md)"
                )
                self.query_one("#select", Button).disabled = True
                self.selected_path = None
            else:
                self.dismiss(self.selected_path)
        else:
            self.dismiss(None)

    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        """Handle Cancel button."""
        self.dismiss(None)

    def key_escape(self) -> None:
        """Handle ESC key."""
        self.dismiss(None)


class MultiSelectFileDialog(ModalScreen[Optional[list[Path]]]):
    """File/directory selection dialog with multi-select.

    - Space: toggle selection
    - Enter: confirm selection (no need to Tab to button)
    - Supports selecting files and/or directories
    """

    CSS = """
    MultiSelectFileDialog {
        align: center middle;
    }
    
    #file-container {
        width: 80;
        height: 30;
        border: thick $background 50%;
        background: $surface;
        padding: 1;
    }
    
    #file-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $text;
        height: 1;
    }
    
    #instructions {
        margin-bottom: 1;
        color: $text-muted;
        height: 2;
    }
    
    #path-display {
        background: $boost;
        padding: 0 1;
        margin-bottom: 1;
        height: 1;
        color: $text;
    }
    
    #file-tree {
        height: 1fr;
        border: solid $primary;
        background: $background;
        margin-bottom: 1;
    }
    
    #button-container {
        align: center middle;
        height: 3;
    }
    
    Button {
        width: 10;
        margin: 0 1;
    }
    """

    def __init__(
        self,
        title: str = "Add Documents",
        start_path: Optional[Path] = None,
        show_dotfiles: bool = False,
        name: Optional[str] = None,
    ) -> None:
        super().__init__(name=name)
        self.title_text = title
        self.start_path = Path(start_path) if start_path else Path.home()
        self.show_dotfiles = show_dotfiles
        self.selected_paths: set[Path] = set()

    def compose(self) -> ComposeResult:
        with Container(id="file-container"):
            yield Label(self.title_text, id="file-title")
            yield Label(
                "Arrows navigate/open. Space: select. Enter: open or confirm.",
                id="instructions",
            )
            yield Static("No selection", id="path-display")
            yield FilteredDirectoryTree(
                self.start_path, show_dotfiles=self.show_dotfiles, id="file-tree"
            )
            with Horizontal(id="button-container"):
                yield Button("Select", variant="primary", id="select")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        tree = self.query_one(Tree)
        # Provide some guides and focus for usability
        try:
            tree.guide_depth = 2  # type: ignore[attr-defined]
        except Exception:
            pass
        tree.focus()

    def _update_status(self) -> None:
        label = (
            f"Selected {len(self.selected_paths)} item(s)"
            if self.selected_paths
            else "No selection"
        )
        self.query_one("#path-display", Static).update(label)

    def _set_node_checked(self, node: TreeNode[Path], checked: bool) -> None:
        if not node or not node.data:
            return
        path: Path = node.data
        # Build base label
        base_label = f"📁 {path.name}" if path.is_dir() else path.name
        prefix = "[x] " if checked else "[ ] "
        node.set_label(prefix + base_label)
        node.refresh()

    def _toggle_current_selection(self) -> None:
        tree = self.query_one(Tree)
        node = getattr(tree, "cursor_node", None)
        if not node or not node.data:
            return
        path: Path = node.data
        if path in self.selected_paths:
            self.selected_paths.remove(path)
            self._set_node_checked(node, False)
        else:
            self.selected_paths.add(path)
            self._set_node_checked(node, True)
        self._last_highlighted = path
        self._update_status()

    def _confirm(self) -> None:
        selection = list(self.selected_paths)
        self.dismiss(selection if selection else None)

    def on_key(self, event: events.Key) -> None:  # type: ignore[override]
        if event.key == "space":
            self._toggle_current_selection()
            event.prevent_default()
            event.stop()
        elif event.key == "enter":
            # Only confirm if the user has explicitly selected items;
            # otherwise, let the tree handle Enter to open/collapse folders.
            if self.selected_paths:
                self._confirm()
                event.prevent_default()
                event.stop()

    @on(Button.Pressed, "#select")
    def on_select_button(self) -> None:
        self._confirm()

    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        self.dismiss(None)

    def key_escape(self) -> None:
        self.dismiss(None)


class CategorySelectDialog(ModalScreen[Optional[str]]):
    """Modal dialog for category selection using a list."""

    CSS = """
    CategorySelectDialog {
        align: center middle;
    }
    
    #category-container {
        width: 50;
        height: 20;
        max-height: 30;
        border: thick $background 50%;
        background: $surface;
        padding: 1 2;
    }
    
    #category-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $text;
        height: 1;
    }
    
    #category-list {
        height: 1fr;
        border: solid $primary;
        background: $background;
        margin-bottom: 1;
    }
    
    ListView > ListItem {
        padding: 0 2;
    }
    
    ListView > ListItem.--highlight {
        background: $accent;
    }
    
    #button-container {
        align: center middle;
        height: 3;
    }
    
    Button {
        width: 10;
        margin: 0 1;
    }
    """

    def __init__(
        self,
        title: str,
        categories: List[str],
        default_category: Optional[str] = None,
        name: Optional[str] = None,
    ):
        """Initialize category selection dialog.

        Args:
            title: Dialog title
            categories: List of categories
            default_category: Default selected category
            name: Screen name
        """
        super().__init__(name=name)
        self.title_text = title
        self.categories = categories
        self.default_category = default_category
        self.selected_category: Optional[str] = default_category

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Container(id="category-container"):
            yield Label(self.title_text, id="category-title")

            # Build items up-front to avoid mounting during compose
            items = [ListItem(Label(category)) for category in self.categories]
            yield ListView(*items, id="category-list")

            with Horizontal(id="button-container"):
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", variant="default", id="cancel")

    def on_mount(self) -> None:
        """Focus list on mount."""
        list_view = self.query_one("#category-list", ListView)
        list_view.focus()
        # Set default selection if provided
        if self.default_category and self.default_category in self.categories:
            try:
                list_view.index = self.categories.index(self.default_category)
            except Exception:
                pass

    @on(ListView.Selected)
    def on_list_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection."""
        if event.item:
            label = event.item.query_one(Label)
            self.selected_category = str(label.renderable)
            self.dismiss(self.selected_category)

    @on(Button.Pressed, "#ok")
    def on_ok(self) -> None:
        """Handle OK button."""
        list_view = self.query_one("#category-list", ListView)
        if list_view.index is not None and 0 <= list_view.index < len(self.categories):
            self.selected_category = self.categories[list_view.index]
            self.dismiss(self.selected_category)
        else:
            self.dismiss(None)

    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        """Handle Cancel button."""
        self.dismiss(None)

    def key_escape(self) -> None:
        """Handle ESC key."""
        self.dismiss(None)


class MessageDialog(ModalScreen[None]):
    """Simple message dialog."""

    CSS = """
    MessageDialog {
        align: center middle;
    }
    
    #message-container {
        width: 60;
        height: auto;
        max-height: 20;
        border: thick $background 50%;
        background: $surface;
        padding: 1 2;
    }
    
    #message-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
        color: $text;
    }
    
    #message-content {
        margin-bottom: 1;
        color: $text;
    }
    
    #button-container {
        align: center middle;
        height: 3;
    }
    
    Button {
        width: 10;
    }
    """

    def __init__(
        self,
        title: str,
        message: str,
        name: Optional[str] = None,
    ):
        """Initialize message dialog.

        Args:
            title: Dialog title
            message: Message to display
            name: Screen name
        """
        super().__init__(name=name)
        self.title_text = title
        self.message_text = message

    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Container(id="message-container"):
            yield Label(self.title_text, id="message-title")
            yield Label(self.message_text, id="message-content")
            with Horizontal(id="button-container"):
                yield Button("OK", variant="primary", id="ok")

    @on(Button.Pressed, "#ok")
    def on_ok(self) -> None:
        """Handle OK button."""
        self.dismiss(None)

    def key_escape(self) -> None:
        """Handle ESC key."""
        self.dismiss(None)

    def key_enter(self) -> None:
        """Handle Enter key."""
        self.dismiss(None)
