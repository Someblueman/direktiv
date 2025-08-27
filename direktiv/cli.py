"""Command-line interface for direktiv."""

from pathlib import Path
from typing import Optional

import click

from .app import DirektivApp


@click.command()
@click.argument(
    "root_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
    required=False,
)
@click.option(
    "--version",
    is_flag=True,
    help="Show version and exit"
)
def main(root_dir: Optional[Path], version: bool) -> None:
    """direktiv - Terminal markdown reader and viewer.
    
    Launch direktiv with the specified ROOT_DIR as the starting directory.
    If no directory is provided, uses the current working directory.
    
    Examples:
    
        direktiv ~/Documents
        
        direktiv /path/to/markdown/files
        
        direktiv  # Uses current directory
    """
    if version:
        from . import __version__
        click.echo(f"direktiv {__version__}")
        return
    
    # Default to current directory if no root_dir specified
    if root_dir is None:
        root_dir = Path.cwd()
    
    # Resolve to absolute path
    root_dir = root_dir.resolve()
    
    # Check if directory is accessible
    if not root_dir.exists():
        click.echo(f"Error: Directory {root_dir} does not exist.", err=True)
        raise click.Abort()
    
    if not root_dir.is_dir():
        click.echo(f"Error: {root_dir} is not a directory.", err=True)
        raise click.Abort()
    
    try:
        # Check if we can read the directory
        list(root_dir.iterdir())
    except PermissionError:
        click.echo(f"Error: Permission denied accessing {root_dir}", err=True)
        raise click.Abort()
    
    # Launch the application
    app = DirektivApp(root_dir=root_dir)
    app.run()


if __name__ == "__main__":
    main()