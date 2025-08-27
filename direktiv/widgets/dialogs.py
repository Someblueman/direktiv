"""Dialog widgets for direktiv TUI."""

from pathlib import Path
from typing import Optional

from textual import on
from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import ModalScreen
from textual.widgets import Button, Input, Label, Select, Static


class InputDialog(ModalScreen[Optional[str]]):
    """Modal dialog for text input."""
    
    CSS = """
    InputDialog {
        align: center middle;
    }
    
    #dialog-container {
        width: 60;
        height: auto;
        border: thick $background 50%;
        background: $surface;
        padding: 1 2;
    }
    
    #dialog-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #dialog-prompt {
        margin-bottom: 1;
    }
    
    #dialog-input {
        width: 100%;
        margin-bottom: 1;
    }
    
    #button-container {
        align: center middle;
        height: auto;
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
        value = self.query_one("#dialog-input", Input).value
        self.dismiss(value if value else None)
    
    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        """Handle Cancel button."""
        self.dismiss(None)
    
    @on(Input.Submitted)
    def on_input_submitted(self) -> None:
        """Handle Enter key in input."""
        value = self.query_one("#dialog-input", Input).value
        self.dismiss(value if value else None)


class FilePickerDialog(ModalScreen[Optional[Path]]):
    """Modal dialog for file selection."""
    
    CSS = """
    FilePickerDialog {
        align: center middle;
    }
    
    #picker-container {
        width: 80;
        height: auto;
        max-height: 30;
        border: thick $background 50%;
        background: $surface;
        padding: 1 2;
    }
    
    #picker-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #path-input {
        width: 100%;
        margin-bottom: 1;
    }
    
    #type-label {
        margin-bottom: 1;
    }
    
    #button-container {
        align: center middle;
        height: auto;
        margin-top: 1;
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
        file_filter: str = "*.md",
        name: Optional[str] = None,
    ):
        """Initialize file picker dialog.
        
        Args:
            title: Dialog title
            start_path: Starting directory
            file_filter: File filter pattern
            name: Screen name
        """
        super().__init__(name=name)
        self.title_text = title
        self.start_path = start_path or Path.home()
        self.file_filter = file_filter
    
    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Container(id="picker-container"):
            yield Label(self.title_text, id="picker-title")
            yield Input(
                value=str(self.start_path),
                placeholder="Enter file path or directory",
                id="path-input"
            )
            yield Label(f"File type: {self.file_filter}", id="type-label")
            with Horizontal(id="button-container"):
                yield Button("Select", variant="primary", id="select")
                yield Button("Cancel", variant="default", id="cancel")
    
    def on_mount(self) -> None:
        """Focus input on mount."""
        self.query_one("#path-input", Input).focus()
    
    @on(Button.Pressed, "#select")
    def on_select(self) -> None:
        """Handle Select button."""
        path_str = self.query_one("#path-input", Input).value
        if path_str:
            path = Path(path_str).expanduser()
            if path.exists():
                self.dismiss(path)
            else:
                # Try to interpret as a file in home directory
                home_path = Path.home() / path_str
                if home_path.exists():
                    self.dismiss(home_path)
                else:
                    self.dismiss(None)
        else:
            self.dismiss(None)
    
    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        """Handle Cancel button."""
        self.dismiss(None)
    
    @on(Input.Submitted)
    def on_input_submitted(self) -> None:
        """Handle Enter key in input."""
        self.on_select()


class CategorySelectDialog(ModalScreen[Optional[str]]):
    """Modal dialog for category selection."""
    
    CSS = """
    CategorySelectDialog {
        align: center middle;
    }
    
    #category-container {
        width: 50;
        height: auto;
        border: thick $background 50%;
        background: $surface;
        padding: 1 2;
    }
    
    #category-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #category-select {
        width: 100%;
        margin-bottom: 1;
    }
    
    #button-container {
        align: center middle;
        height: auto;
    }
    
    Button {
        width: 10;
        margin: 0 1;
    }
    """
    
    def __init__(
        self,
        title: str,
        categories: list[str],
        default_category: str = "General",
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
    
    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Container(id="category-container"):
            yield Label(self.title_text, id="category-title")
            
            # Create options for Select widget
            options = [(cat, cat) for cat in self.categories]
            
            yield Select(
                options=options,
                value=self.default_category if self.default_category in self.categories else None,
                id="category-select",
                allow_blank=False
            )
            
            with Horizontal(id="button-container"):
                yield Button("OK", variant="primary", id="ok")
                yield Button("Cancel", variant="default", id="cancel")
    
    def on_mount(self) -> None:
        """Focus select on mount."""
        self.query_one("#category-select", Select).focus()
    
    @on(Button.Pressed, "#ok")
    def on_ok(self) -> None:
        """Handle OK button."""
        selected = self.query_one("#category-select", Select).value
        self.dismiss(selected)
    
    @on(Button.Pressed, "#cancel")
    def on_cancel(self) -> None:
        """Handle Cancel button."""
        self.dismiss(None)


class ConfirmDialog(ModalScreen[bool]):
    """Modal dialog for confirmation."""
    
    CSS = """
    ConfirmDialog {
        align: center middle;
    }
    
    #confirm-container {
        width: 50;
        height: auto;
        border: thick $background 50%;
        background: $surface;
        padding: 1 2;
    }
    
    #confirm-title {
        text-align: center;
        text-style: bold;
        margin-bottom: 1;
    }
    
    #confirm-message {
        text-align: center;
        margin-bottom: 1;
    }
    
    #button-container {
        align: center middle;
        height: auto;
    }
    
    Button {
        width: 10;
        margin: 0 1;
    }
    """
    
    def __init__(
        self,
        title: str,
        message: str,
        name: Optional[str] = None,
    ):
        """Initialize confirmation dialog.
        
        Args:
            title: Dialog title
            message: Confirmation message
            name: Screen name
        """
        super().__init__(name=name)
        self.title_text = title
        self.message_text = message
    
    def compose(self) -> ComposeResult:
        """Compose the dialog."""
        with Container(id="confirm-container"):
            yield Label(self.title_text, id="confirm-title")
            yield Label(self.message_text, id="confirm-message")
            with Horizontal(id="button-container"):
                yield Button("Yes", variant="primary", id="yes")
                yield Button("No", variant="default", id="no")
    
    @on(Button.Pressed, "#yes")
    def on_yes(self) -> None:
        """Handle Yes button."""
        self.dismiss(True)
    
    @on(Button.Pressed, "#no")
    def on_no(self) -> None:
        """Handle No button."""
        self.dismiss(False)