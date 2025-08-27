"""Document management operations for direktiv."""

import hashlib
import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class DocumentManager:
    """Manages the document library for direktiv."""

    def __init__(self, library_path: Optional[Path] = None, show_dotfiles: bool = False):
        """Initialize document manager.
        
        Args:
            library_path: Path to document library. Defaults to ~/.direktiv/documents
            show_dotfiles: Whether to show dotfiles (hidden directories)
        """
        if library_path is None:
            library_path = Path.home() / ".direktiv" / "documents"
        
        self.library_path = library_path
        self.library_path.mkdir(parents=True, exist_ok=True)
        self.show_dotfiles = show_dotfiles
        
        # Create General category by default
        self._ensure_default_categories()

    def _ensure_default_categories(self) -> None:
        """Ensure default categories exist."""
        default_categories = ["General", "Personal", "Work"]
        for category in default_categories:
            category_path = self.library_path / category
            category_path.mkdir(exist_ok=True)

    def add_document(
        self, 
        source_path: Path, 
        category: str = "General",
        title: Optional[str] = None
    ) -> Tuple[bool, str, Optional[Path]]:
        """Add a document to the library.
        
        Args:
            source_path: Path to source markdown file
            category: Category to add document to
            title: Optional custom title for the document
            
        Returns:
            Tuple of (success, message, library_path)
        """
        # Validate source
        if not source_path.exists():
            return False, f"File {source_path} does not exist", None
        
        if source_path.suffix.lower() != '.md':
            return False, "Only markdown files (.md) are supported", None
        
        # Ensure category exists
        category_path = self.library_path / category
        category_path.mkdir(exist_ok=True)
        
        # Generate unique filename if needed
        dest_name = title if title else source_path.name
        if not dest_name.endswith('.md'):
            dest_name += '.md'
        
        dest_path = category_path / dest_name
        
        # Handle duplicates
        if dest_path.exists():
            # Check if it's the same file
            if self._are_files_identical(source_path, dest_path):
                return False, "Document already exists in library", dest_path
            
            # Generate unique name
            counter = 1
            while dest_path.exists():
                name_stem = dest_path.stem
                dest_path = category_path / f"{name_stem}_{counter}.md"
                counter += 1
        
        # Copy file
        try:
            shutil.copy2(source_path, dest_path)
            return True, f"Added {dest_name} to {category}", dest_path
        except Exception as e:
            return False, f"Failed to add document: {e}", None

    def _are_files_identical(self, file1: Path, file2: Path) -> bool:
        """Check if two files are identical using hash.
        
        Args:
            file1: First file path
            file2: Second file path
            
        Returns:
            True if files have same content
        """
        try:
            with open(file1, 'rb') as f1:
                hash1 = hashlib.md5(f1.read()).hexdigest()
            with open(file2, 'rb') as f2:
                hash2 = hashlib.md5(f2.read()).hexdigest()
            return hash1 == hash2
        except Exception:
            return False

    def create_category(self, name: str) -> Tuple[bool, str]:
        """Create a new category.
        
        Args:
            name: Category name
            
        Returns:
            Tuple of (success, message)
        """
        if not name or name.strip() == "":
            return False, "Category name cannot be empty"
        
        # Sanitize name
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        if not safe_name:
            return False, "Invalid category name"
        
        category_path = self.library_path / safe_name
        if category_path.exists():
            return False, f"Category '{safe_name}' already exists"
        
        try:
            category_path.mkdir(parents=True)
            return True, f"Created category '{safe_name}'"
        except Exception as e:
            return False, f"Failed to create category: {e}"

    def list_categories(self) -> List[str]:
        """List all categories.
        
        Returns:
            List of category names
        """
        categories = []
        for item in self.library_path.iterdir():
            if item.is_dir():
                # Skip dotfiles unless show_dotfiles is True
                if not self.show_dotfiles and item.name.startswith('.'):
                    continue
                categories.append(item.name)
        return sorted(categories)

    def list_documents(self, category: Optional[str] = None) -> List[Dict[str, str]]:
        """List all documents in library.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of document info dicts
        """
        documents = []
        
        if category:
            categories = [category] if (self.library_path / category).exists() else []
        else:
            categories = self.list_categories()
        
        for cat in categories:
            cat_path = self.library_path / cat
            for file_path in cat_path.glob("*.md"):
                documents.append({
                    "path": str(file_path),
                    "name": file_path.name,
                    "category": cat,
                    "size": file_path.stat().st_size,
                    "modified": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat()
                })
        
        return sorted(documents, key=lambda x: (x["category"], x["name"]))

    def move_document(
        self, 
        document_path: Path, 
        new_category: str
    ) -> Tuple[bool, str]:
        """Move a document to a different category.
        
        Args:
            document_path: Path to document in library
            new_category: Target category
            
        Returns:
            Tuple of (success, message)
        """
        if not document_path.exists():
            return False, "Document not found"
        
        # Ensure document is in library
        try:
            document_path.relative_to(self.library_path)
        except ValueError:
            return False, "Document is not in library"
        
        # Create category if needed
        category_path = self.library_path / new_category
        category_path.mkdir(exist_ok=True)
        
        # Move file
        new_path = category_path / document_path.name
        if new_path.exists():
            return False, f"Document already exists in {new_category}"
        
        try:
            shutil.move(str(document_path), str(new_path))
            return True, f"Moved to {new_category}"
        except Exception as e:
            return False, f"Failed to move: {e}"

    def delete_document(self, document_path: Path) -> Tuple[bool, str]:
        """Delete a document from the library.
        
        Args:
            document_path: Path to document
            
        Returns:
            Tuple of (success, message)
        """
        if not document_path.exists():
            return False, "Document not found"
        
        # Ensure document is in library
        try:
            document_path.relative_to(self.library_path)
        except ValueError:
            return False, "Document is not in library"
        
        try:
            document_path.unlink()
            return True, "Document deleted"
        except Exception as e:
            return False, f"Failed to delete: {e}"

    def import_directory(
        self, 
        source_dir: Path, 
        category: Optional[str] = None,
        recursive: bool = True
    ) -> Tuple[int, int, List[str]]:
        """Import all markdown files from a directory.
        
        Args:
            source_dir: Source directory path
            category: Category for imported files (uses subdirs as categories if None)
            recursive: Whether to search recursively
            
        Returns:
            Tuple of (success_count, fail_count, messages)
        """
        if not source_dir.exists() or not source_dir.is_dir():
            return 0, 0, [f"Directory {source_dir} does not exist"]
        
        success_count = 0
        fail_count = 0
        messages = []
        
        pattern = "**/*.md" if recursive else "*.md"
        
        for md_file in source_dir.glob(pattern):
            # Determine category
            if category:
                target_category = category
            else:
                # Use immediate parent dir as category
                parent = md_file.parent
                if parent == source_dir:
                    target_category = "General"
                else:
                    target_category = parent.name
            
            # Add document
            success, msg, _ = self.add_document(md_file, target_category)
            if success:
                success_count += 1
            else:
                fail_count += 1
            messages.append(f"{md_file.name}: {msg}")
        
        return success_count, fail_count, messages

    def export_library(self, export_path: Path) -> Tuple[bool, str]:
        """Export the entire library structure.
        
        Args:
            export_path: Path to export to
            
        Returns:
            Tuple of (success, message)
        """
        if export_path.exists():
            return False, "Export path already exists"
        
        try:
            shutil.copytree(self.library_path, export_path)
            doc_count = sum(1 for _ in self.library_path.rglob("*.md"))
            return True, f"Exported {doc_count} documents to {export_path}"
        except Exception as e:
            return False, f"Export failed: {e}"

    def search_documents(self, query: str) -> List[Dict[str, str]]:
        """Search for documents by filename.
        
        Args:
            query: Search query (case-insensitive)
            
        Returns:
            List of matching documents
        """
        query_lower = query.lower()
        matches = []
        
        for doc in self.list_documents():
            if query_lower in doc["name"].lower():
                matches.append(doc)
        
        return matches

    def get_library_stats(self) -> Dict[str, int]:
        """Get library statistics.
        
        Returns:
            Dictionary with stats
        """
        stats = {
            "total_documents": 0,
            "total_categories": len(self.list_categories()),
            "total_size_bytes": 0
        }
        
        for category in self.list_categories():
            cat_path = self.library_path / category
            for md_file in cat_path.glob("*.md"):
                stats["total_documents"] += 1
                stats["total_size_bytes"] += md_file.stat().st_size
        
        stats["total_size_mb"] = round(stats["total_size_bytes"] / (1024 * 1024), 2)
        
        return stats