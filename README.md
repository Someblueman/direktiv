# direktiv

Personal markdown library for your terminal.

## What It Does

direktiv keeps all your markdown in one tidy place at `~/.direktiv/documents/`. Browse by category, read with a clean TUI, and track what you’ve read — all from the keyboard.

- Centralized library with categories (General, Work, Personal, …)
- TUI reader with keyboard shortcuts and clean rendering
- Read/unread tracking stored in a lightweight database
- Simple CLI to add, import, list, and export

## Install

```bash
pip install direktiv
```

## Quick Start

```bash
# Open the TUI
direktiv

# Add files (CLI)
direktiv add README.md                     # -> General
direktiv add notes.md -c Personal -t "Notes"

# Import a folder
direktiv import ~/Documents/wiki           # recursive by default

# Browse your library
direktiv list                              # --category Work | --search readme
```

In the TUI:
- Arrows/Enter: Navigate and open
- Space: Toggle read/unread
- a: Add documents (multi-select files or directories)
- .: Show/Hide hidden files
- r: Refresh  •  ?: Help  •  q/Ctrl+C: Quit

## Screenshot

![direktiv TUI](docs/screenshot.gif)

Recorded with VHS. Tape at `docs/direktiv.tape`.

## Commands (essentials)

- `direktiv add <file> [-c <category>] [-t <title>]`
- `direktiv import <dir> [-c <category>] [--no-recursive]`
- `direktiv list [--category <name>] [--search <text>]`
- `direktiv stats`  •  `direktiv categories`  •  `direktiv export <path>`

Run `direktiv --help` or any subcommand with `--help` for details.

## Library Layout

```
~/.direktiv/
├── documents/       # Your markdown library (by category)
├── database.db      # Read status + metadata
└── config.json      # Preferences
```

## Configuration

User settings live in `~/.direktiv/config.json` (theme, default category, timers, etc.). Sensible defaults are provided; adjust as needed.

## Changelog

See CHANGELOG.md for release notes.

## Development

```bash
pip install -e ".[dev]"
pytest
black direktiv/ && isort direktiv/
```

## Contributing

Contributions welcome — please open a PR.

## License

MIT
