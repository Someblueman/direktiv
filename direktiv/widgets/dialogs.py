"""Dialog widgets for direktiv TUI."""

import os
from pathlib import Path
from typing import Optional, List

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Static, DirectoryTree, ListView, ListItem


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
                id="dialog-input"
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
        self.selected_path: Optional[Path] = None
    
    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Container(id="file-container"):
            yield Label(self.title_text, id="file-title")
            
            if self.select_directory:
                yield Label(
                    "Navigate and select a directory, then click Select.",
                    id="instructions"
                )
            else:
                yield Label(
                    "Navigate and select a markdown file (.md), then click Select.",
                    id="instructions"
                )
            
            yield Static("No selection", id="path-display")
            
            yield DirectoryTree(
                self.start_path,
                id="file-tree"
            )
            
            with Horizontal(id="button-container"):
                yield Button("Select", variant="primary", id="select", disabled=True)
                yield Button("Cancel", variant="default", id="cancel")
    
    def on_mount(self) -> None:
        """Initialize on mount."""
        tree = self.query_one(DirectoryTree)
        tree.show_root = False
        tree.guide_depth = 2
        tree.focus()
    
    @on(DirectoryTree.FileSelected)
    def on_file_selected(self, event: DirectoryTree.FileSelected) -> None:
        """Handle file selection."""
        if not self.select_directory:
            self.selected_path = event.path
            self.query_one("#path-display", Static).update(f"Selected: {event.path.name}")
            self.query_one("#select", Button).disabled = False
    
    @on(DirectoryTree.DirectorySelected)
    def on_directory_selected(self, event: DirectoryTree.DirectorySelected) -> None:
        """Handle directory selection."""
        if self.select_directory:
            self.selected_path = event.path
            self.query_one("#path-display", Static).update(f"Selected: {event.path.name}")
            self.query_one("#select", Button).disabled = False
    
    @on(Button.Pressed, "#select")
    def on_select(self) -> None:
        """Handle Select button."""
        if self.selected_path:
            # Additional validation for markdown files
            if not self.select_directory and self.selected_path.suffix.lower() != '.md':
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
            
            list_view = ListView(id="category-list")
            for category in self.categories:
                list_item = ListItem(Label(category))
                list_view.append(list_item)
                if category == self.default_category:
                    list_view.index = self.categories.index(category)
            
            yield list_view
            
            with Horizontal(id="button-container"):
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", variant="default", id="cancel")
    
    def on_mount(self) -> None:
        """Focus list on mount."""
        self.query_one("#category-list", ListView).focus()
    
    @on(ListView.Selected)
    def on_list_selected(self, event: ListView.Selected) -> None:
        """Handle list item selection."""
        if event.item:
            label = event.item.query_one(Label)
            self.selected_category = label.renderable
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