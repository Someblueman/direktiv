# direktiv

A simple and elegant terminal markdown reader/viewer built with Python and Textual.

## Features

- **Two-pane interface**: File browser on the left, markdown viewer on the right
- **Hierarchical file browsing**: Navigate through directories and subdirectories
- **Read status tracking**: Mark files as read/unread with visual indicators
- **Beautiful markdown rendering**: Syntax highlighting, tables, lists, and more
- **Vim-style navigation**: Use familiar keybindings for scrolling
- **File operations**: Add, delete, and organize your markdown files
- **Cross-platform**: Works on macOS, Linux, and Windows

## Installation

```bash
# Install from source
git clone https://github.com/yourusername/direktiv.git
cd direktiv
pip install -e .

# Or install from PyPI (when published)
pip install direktiv
```

## Usage

```bash
# Launch with current directory
direktiv

# Launch with specific directory
direktiv ~/Documents

# Launch with any path
direktiv /path/to/markdown/files

# Show version
direktiv --version
```

## Controls

### Navigation
- **Arrow keys**: Navigate the file tree
- **Enter**: Open selected file
- **Tab**: Switch between panes

### File Operations
- **Space**: Toggle read/unread status
- **Delete**: Delete selected file
- **Ctrl+N**: Add new file (copy from elsewhere)

### Viewer Controls
- **j/k**: Scroll up/down (vim-style)
- **Page Up/Down**: Page navigation
- **Home/End**: Jump to top/bottom
- **g**: Go to top
- **Shift+G**: Go to bottom

### Global Controls
- **r**: Refresh file tree
- **h**: Show help
- **q** or **Ctrl+C**: Quit

## File Status Indicators

- **●** Unread file
- **✓** Read file
- **🗂️** Directory

## Configuration

direktiv stores its database in `~/.direktiv/database.db` to track read status across sessions.

## Development

```bash
# Clone the repository
git clone https://github.com/yourusername/direktiv.git
cd direktiv

# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=direktiv

# Format code
black direktiv/
isort direktiv/

# Type checking
mypy direktiv/
```

## Requirements

- Python 3.10+
- Terminal with color support
- Modern terminal emulator recommended for best experience

## License

MIT License - see LICENSE file for details.