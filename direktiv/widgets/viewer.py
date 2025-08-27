"""Markdown viewer widget for direktiv."""

from pathlib import Path
from typing import Optional

from rich.console import RenderableType
from rich.markdown import Markdown
from rich.text import Text
from textual.widgets import Static
from textual.reactive import reactive
from textual.containers import VerticalScroll


class MarkdownViewer(VerticalScroll):
    """A widget for viewing markdown content."""

    current_file: reactive[Optional[Path]] = reactive(None)

    def __init__(self, **kwargs) -> None:
        """Initialize the markdown viewer."""
        super().__init__(**kwargs)
        self._content_widget: Optional[Static] = None
        self.border_title = "Markdown Viewer"
        self.can_focus = True

    def on_mount(self) -> None:
        """Called when the widget is mounted."""
        self.show_content(
            "Welcome to direktiv\n\nSelect a markdown file from the left pane to view it here.",
            is_markdown=True,
        )

    def show_content(self, content: str, is_markdown: bool = True) -> None:
        """Display content in the viewer.

        Args:
            content: Content to display
            is_markdown: Whether to render as markdown
        """
        try:
            if is_markdown:
                # Render as markdown using Rich
                renderable = Markdown(content, code_theme="monokai")
            else:
                # Render as plain text
                renderable = Text(content)

            # Remove existing content widget if present
            if self._content_widget:
                self._content_widget.remove()

            # Create new content widget
            self._content_widget = Static(renderable)
            self.mount(self._content_widget)

            # Scroll to top when new content is loaded
            self.scroll_home()

        except Exception as e:
            # Show error message if rendering fails
            error_text = f"Error rendering content: {str(e)}\n\nRaw content:\n{content}"

            # Remove existing content widget if present
            if self._content_widget:
                self._content_widget.remove()

            self._content_widget = Static(Text(error_text))
            self.mount(self._content_widget)

    def show_file(self, file_path: Path) -> None:
        """Load and display a markdown file.

        Args:
            file_path: Path to the markdown file
        """
        try:
            self.current_file = file_path
            content = file_path.read_text(encoding="utf-8")
            self.show_content(content, is_markdown=True)
        except FileNotFoundError:
            self.show_content(f"File not found: {file_path}", is_markdown=False)
        except PermissionError:
            self.show_content(f"Permission denied: {file_path}", is_markdown=False)
        except UnicodeDecodeError:
            self.show_content(f"Unable to decode file: {file_path}", is_markdown=False)
        except Exception as e:
            self.show_content(f"Error loading file: {e}", is_markdown=False)

    def clear_content(self) -> None:
        """Clear the viewer content."""
        if self._content_widget:
            self._content_widget.remove()
            self._content_widget = None
        self.current_file = None

    def get_current_file(self) -> Optional[Path]:
        """Get the currently displayed file.

        Returns:
            Path to current file or None
        """
        return self.current_file

    async def key_home(self) -> None:
        """Handle Home key - scroll to top."""
        self.scroll_home()

    async def key_end(self) -> None:
        """Handle End key - scroll to bottom."""
        self.scroll_end()

    async def key_page_up(self) -> None:
        """Handle Page Up key."""
        self.scroll_page_up()

    async def key_page_down(self) -> None:
        """Handle Page Down key."""
        self.scroll_page_down()

    async def key_j(self) -> None:
        """Handle j key - scroll down (vim-style)."""
        self.scroll_down()

    async def key_k(self) -> None:
        """Handle k key - scroll up (vim-style)."""
        self.scroll_up()

    async def key_g(self) -> None:
        """Handle g key - scroll to top (vim-style)."""
        self.scroll_home()

    async def key_shift_g(self) -> None:
        """Handle Shift+G key - scroll to bottom (vim-style)."""
        self.scroll_end()

    def watch_current_file(
        self, old_file: Optional[Path], new_file: Optional[Path]
    ) -> None:
        """React to current file changes.

        Args:
            old_file: Previous file
            new_file: New file
        """
        if new_file and new_file != old_file:
            self.show_file(new_file)
