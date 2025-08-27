# Features Overview

direktiv is designed to be a simple yet powerful markdown reader for the terminal.

## Core Features

### Two-Pane Interface
- Left pane: File browser with hierarchical view
- Right pane: Markdown content viewer (70-80% width)
- Clean, distraction-free interface

### Read Status Tracking
- **●** Unread files (shown in file tree)
- **✓** Read files (marked when you toggle status)
- Persistent across sessions using SQLite database

### File Operations
- **Space**: Toggle read/unread status
- **Delete**: Remove selected file
- **Insert**: Add new file (copy from elsewhere)

### Navigation
- **Arrow keys**: Navigate file tree
- **Enter**: Open selected file
- **j/k**: Scroll content up/down (vim-style)
- **Page Up/Down**: Page through content
- **Home/End**: Jump to top/bottom

### Global Controls
- **r**: Refresh file tree
- **h**: Show help
- **q** or **Ctrl+C**: Quit application

## Technical Features

### Markdown Rendering
- Full CommonMark support via Rich library
- Syntax highlighting for code blocks
- Tables, lists, links, and formatting
- Configurable themes

### Performance
- Lazy loading for large directories
- Efficient file watching
- Minimal memory footprint

### Cross-Platform
- Works on macOS, Linux, and Windows
- Modern terminal emulator recommended
- No external dependencies beyond Python