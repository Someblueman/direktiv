# direktiv

A personal markdown document manager for your terminal.

## Overview

direktiv v0.3.0 is a terminal-based markdown document manager that provides a centralized library for all your markdown files. Instead of browsing directories, direktiv maintains its own organized document library in `~/.direktiv/documents/`, allowing you to categorize and manage your markdown documents from one place.

## Features

- **Centralized Library**: All documents stored in `~/.direktiv/documents/`
- **Category Organization**: Organize documents into categories (General, Work, Personal, etc.)
- **TUI Viewer**: Beautiful terminal interface for reading markdown
- **Read/Unread Tracking**: Keep track of which documents you've read
- **CLI Commands**: Add, import, list, and manage documents from the command line
- **Add Documents (TUI)**: Multi-select files or select a directory to import all `.md` files
- **Document Import (CLI)**: Bulk import existing markdown files via command
- **Statistics**: Track your reading progress and library stats

## Installation

```bash
pip install direktiv
```

## Usage

### Launch the TUI Viewer

```bash
# Launch the interactive viewer
direktiv
```

In the viewer:
- Arrow keys: Navigate categories and documents
- Enter: Open document / expand-collapse folders
- Space: Mark document as read/unread
- a: Add documents (multi-select; Space selects, Enter confirms)
- .: Toggle hidden files/folders
- r: Refresh library
- ?: Show help
- q/Ctrl+C: Quit

### CLI Commands

#### Add a Document

```bash
# Add to default category (General)
direktiv add README.md

# Add to specific category
direktiv add notes.md --category Personal

# Add with custom title
direktiv add doc.md -c Work -t "Meeting Notes"
```

#### Create Categories

```bash
direktiv new-category "Project Documentation"
direktiv new-category Research
```

#### Import Documents

```bash
# Import directory recursively
direktiv import ~/Documents/markdown

# Import to specific category
direktiv import ./docs --category Documentation

# Import non-recursively
direktiv import ./notes --no-recursive
```

#### List Documents

```bash
# List all documents
direktiv list

# Filter by category
direktiv list --category Work

# Search by filename
direktiv list --search readme
```

#### View Statistics

```bash
# Show library statistics
direktiv stats

# List all categories
direktiv categories
```

#### Export Library

```bash
# Export entire library
direktiv export ~/backup/my-documents
```

## Library Structure

Your documents are organized in:

```
~/.direktiv/
├── documents/       # Your markdown library
│   ├── General/
│   ├── Personal/
│   ├── Work/
│   └── [Custom Categories]/
├── database.db      # Document metadata & read status
└── config.json      # User preferences
```

## Configuration

Configuration is stored in `~/.direktiv/config.json` and includes:
- Default category for new documents
- Theme preferences
- Auto-mark as read timer
- Category icons and colors

## Upgrading

- v0.3.0: Unified “Add Documents” in the TUI with multi-select. Use `a` to add files or directories (directories import all `.md` recursively). Hidden toggle now affects the selection dialog.
- v0.2.0: Introduced the document library concept. Use the `import` command to bring existing markdown files into your library.

## Development

```bash
# Install in development mode
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black direktiv/ && isort direktiv/
```

## License

MIT License

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.
