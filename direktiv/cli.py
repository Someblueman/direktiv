"""Command-line interface for direktiv."""

from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.table import Table

from .app import DirektivApp
from .database import Database
from .document_manager import DocumentManager

console = Console()


@click.group(invoke_without_command=True)
@click.pass_context
@click.option("--version", is_flag=True, help="Show version and exit")
def main(ctx: click.Context, version: bool) -> None:
    """direktiv - Personal markdown document manager.

    Launch the TUI viewer when no command is specified.
    """
    if version:
        from . import __version__

        click.echo(f"direktiv {__version__}")
        return

    # If no subcommand, launch the TUI
    if ctx.invoked_subcommand is None:
        launch_app()


def launch_app() -> None:
    """Launch the TUI application."""
    library_path = Path.home() / ".direktiv" / "documents"
    library_path.mkdir(parents=True, exist_ok=True)

    # Launch the application with library path
    app = DirektivApp(root_dir=library_path)
    app.run()


@main.command()
@click.argument(
    "file_path",
    type=click.Path(exists=True, file_okay=True, dir_okay=False, path_type=Path),
    required=True,
)
@click.option(
    "--category",
    "-c",
    default="General",
    help="Category to add the document to (default: General)",
)
@click.option("--title", "-t", help="Custom title for the document")
def add(file_path: Path, category: str, title: Optional[str]) -> None:
    """Add a markdown file to your library.

    Examples:
        direktiv add README.md
        direktiv add docs/guide.md --category Documentation
        direktiv add notes.md -c Personal -t "My Notes"
    """
    manager = DocumentManager()
    database = Database()

    success, message, library_path = manager.add_document(file_path, category, title)

    if success and library_path:
        # Add to database
        database.add_document(
            str(library_path),
            category=category,
            original_path=str(file_path),
            title=title,
        )
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        raise click.Abort()


@main.command(name="new-category")
@click.argument("name", required=True)
def new_category(name: str) -> None:
    """Create a new category for organizing documents.

    Examples:
        direktiv new-category "Project Notes"
        direktiv new-category Research
    """
    manager = DocumentManager()

    success, message = manager.create_category(name)

    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        raise click.Abort()


@main.command(name="import")
@click.argument(
    "directory",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
)
@click.option(
    "--category",
    "-c",
    help="Import all files into this category (otherwise uses subdirectories)",
)
@click.option(
    "--recursive/--no-recursive",
    "-r/-R",
    default=True,
    help="Recursively import from subdirectories (default: recursive)",
)
def import_directory(directory: Path, category: Optional[str], recursive: bool) -> None:
    """Import markdown files from a directory.

    Examples:
        direktiv import ~/Documents/notes
        direktiv import ./docs --category Documentation
        direktiv import ./project --no-recursive
    """
    manager = DocumentManager()
    database = Database()

    console.print(f"Importing markdown files from [cyan]{directory}[/cyan]...")

    success_count, fail_count, messages = manager.import_directory(
        directory, category, recursive
    )

    # Update database for imported files
    for doc in manager.list_documents():
        if not database.get_document_info(doc["path"]):
            database.add_document(
                doc["path"], category=doc["category"], original_path=None
            )

    console.print(f"\n[green]✓[/green] Imported {success_count} document(s)")
    if fail_count > 0:
        console.print(f"[yellow]⚠[/yellow] Failed to import {fail_count} document(s)")

    if len(messages) <= 10:
        for msg in messages:
            console.print(f"  • {msg}")
    else:
        console.print(f"  (Showing first 10 of {len(messages)} results)")
        for msg in messages[:10]:
            console.print(f"  • {msg}")


@main.command()
@click.option("--category", "-c", help="Filter by category")
@click.option("--search", "-s", help="Search documents by filename")
def list(category: Optional[str], search: Optional[str]) -> None:
    """List all documents in your library.

    Examples:
        direktiv list
        direktiv list --category Work
        direktiv list --search readme
    """
    manager = DocumentManager()
    database = Database()

    if search:
        documents = manager.search_documents(search)
    else:
        documents = manager.list_documents(category)

    if not documents:
        if search:
            console.print(f"No documents found matching '{search}'")
        elif category:
            console.print(f"No documents in category '{category}'")
        else:
            console.print("No documents in library. Use 'direktiv add' to add some!")
        return

    # Create table
    table = Table(title="Documents Library")
    table.add_column("Category", style="cyan")
    table.add_column("Document", style="white")
    table.add_column("Status", style="green")
    table.add_column("Size", justify="right")

    for doc in documents:
        # Get read status from database
        doc_info = database.get_document_info(doc["path"])
        status = "✓ Read" if doc_info and doc_info.get("is_read") else "● Unread"

        # Format size
        size_bytes = int(doc["size"])
        size_kb = size_bytes / 1024.0
        if size_kb < 1:
            size_str = f"{size_bytes} B"
        elif size_kb < 1024:
            size_str = f"{size_kb:.1f} KB"
        else:
            size_str = f"{size_kb/1024:.1f} MB"

        table.add_row(doc["category"], doc["name"], status, size_str)

    console.print(table)

    # Show statistics
    stats = manager.get_library_stats()
    console.print(
        f"\nTotal: {stats['total_documents']} documents in {stats['total_categories']} categories"
    )


@main.command()
def stats() -> None:
    """Show library statistics.

    Example:
        direktiv stats
    """
    manager = DocumentManager()
    database = Database()

    lib_stats = manager.get_library_stats()
    db_stats = database.get_statistics()

    console.print("\n[bold cyan]Library Statistics[/bold cyan]")
    console.print(f"Total documents: {lib_stats['total_documents']}")
    console.print(f"Total categories: {lib_stats['total_categories']}")
    console.print(f"Total size: {lib_stats['total_size_mb']} MB")

    console.print("\n[bold cyan]Reading Statistics[/bold cyan]")
    console.print(
        f"Documents read: {db_stats['read_documents']}/{db_stats['total_documents']}"
    )

    if db_stats["total_documents"] > 0:
        read_percentage = (
            db_stats["read_documents"] / db_stats["total_documents"]
        ) * 100
        console.print(f"Reading progress: {read_percentage:.1f}%")

    if db_stats["documents_by_category"]:
        console.print("\n[bold cyan]Documents by Category[/bold cyan]")
        for cat_stat in db_stats["documents_by_category"]:
            console.print(f"  {cat_stat['category']}: {cat_stat['count']}")


@main.command()
def categories() -> None:
    """List all categories.

    Example:
        direktiv categories
    """
    manager = DocumentManager()
    categories = manager.list_categories()

    if not categories:
        console.print("No categories found.")
        return

    console.print("[bold cyan]Categories[/bold cyan]")
    for cat in categories:
        doc_count = len(manager.list_documents(cat))
        console.print(f"  • {cat} ({doc_count} documents)")


@main.command()
@click.argument(
    "export_path",
    type=click.Path(exists=False, file_okay=False, dir_okay=True, path_type=Path),
    required=True,
)
def export(export_path: Path) -> None:
    """Export your library to a directory.

    Example:
        direktiv export ~/backup/direktiv-library
    """
    manager = DocumentManager()

    success, message = manager.export_library(export_path)

    if success:
        console.print(f"[green]✓[/green] {message}")
    else:
        console.print(f"[red]✗[/red] {message}")
        raise click.Abort()


if __name__ == "__main__":
    main()
