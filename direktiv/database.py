"""Database operations for direktiv."""

import json
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional


class Database:
    """SQLite database for document metadata and read status."""

    def __init__(self, db_path: Optional[Path] = None) -> None:
        """Initialize database connection.
        
        Args:
            db_path: Path to database file. If None, uses default location.
        """
        if db_path is None:
            # Store in user's home directory
            db_path = Path.home() / ".direktiv" / "database.db"
            db_path.parent.mkdir(exist_ok=True)
        
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """Initialize database tables."""
        with sqlite3.connect(self.db_path) as conn:
            # Create documents table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS documents (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    original_path TEXT,
                    library_path TEXT UNIQUE NOT NULL,
                    category TEXT DEFAULT 'General',
                    title TEXT,
                    is_read BOOLEAN DEFAULT FALSE,
                    date_added TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_opened TIMESTAMP,
                    tags TEXT,
                    notes TEXT
                )
            """)
            
            # Create categories table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS categories (
                    name TEXT PRIMARY KEY,
                    color TEXT,
                    icon TEXT,
                    sort_order INTEGER DEFAULT 0,
                    date_created TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Create index for better performance
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_category 
                ON documents(category)
            """)
            
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_documents_is_read 
                ON documents(is_read)
            """)
            
            conn.commit()

    def add_document(
        self, 
        library_path: str,
        category: str = "General",
        original_path: Optional[str] = None,
        title: Optional[str] = None
    ) -> bool:
        """Add a document to the database.
        
        Args:
            library_path: Path to document in library
            category: Document category
            original_path: Original source path
            title: Optional document title
            
        Returns:
            True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            try:
                conn.execute("""
                    INSERT OR REPLACE INTO documents 
                    (library_path, category, original_path, title, is_read, date_added)
                    VALUES (?, ?, ?, ?, FALSE, CURRENT_TIMESTAMP)
                """, (library_path, category, original_path, title))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def mark_as_read(self, library_path: str) -> None:
        """Mark a document as read.
        
        Args:
            library_path: Path to document in library
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE documents 
                SET is_read = TRUE, last_opened = ?
                WHERE library_path = ?
            """, (datetime.now().isoformat(), library_path))
            conn.commit()

    def mark_as_unread(self, library_path: str) -> None:
        """Mark a document as unread.
        
        Args:
            library_path: Path to document in library
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE documents 
                SET is_read = FALSE
                WHERE library_path = ?
            """, (library_path,))
            conn.commit()

    def is_read(self, library_path: str) -> bool:
        """Check if a document is marked as read.
        
        Args:
            library_path: Path to document in library
            
        Returns:
            True if document is read, False otherwise
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT is_read FROM documents WHERE library_path = ?",
                (library_path,)
            )
            result = cursor.fetchone()
            return bool(result[0]) if result else False

    def update_last_opened(self, library_path: str) -> None:
        """Update the last opened timestamp for a document.
        
        Args:
            library_path: Path to document in library
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                UPDATE documents 
                SET last_opened = ?
                WHERE library_path = ?
            """, (datetime.now().isoformat(), library_path))
            conn.commit()

    def get_document_info(self, library_path: str) -> Optional[Dict]:
        """Get complete information for a document.
        
        Args:
            library_path: Path to document in library
            
        Returns:
            Dictionary with document information or None
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM documents 
                WHERE library_path = ?
            """, (library_path,))
            row = cursor.fetchone()
            
            if row:
                return dict(row)
            return None

    def list_documents(self, category: Optional[str] = None) -> List[Dict]:
        """List all documents, optionally filtered by category.
        
        Args:
            category: Optional category filter
            
        Returns:
            List of document dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            
            if category:
                cursor = conn.execute("""
                    SELECT * FROM documents 
                    WHERE category = ?
                    ORDER BY title, library_path
                """, (category,))
            else:
                cursor = conn.execute("""
                    SELECT * FROM documents 
                    ORDER BY category, title, library_path
                """)
            
            return [dict(row) for row in cursor.fetchall()]

    def delete_document(self, library_path: str) -> bool:
        """Remove a document from the database.
        
        Args:
            library_path: Path to document in library
            
        Returns:
            True if document was deleted
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                DELETE FROM documents 
                WHERE library_path = ?
            """, (library_path,))
            conn.commit()
            return cursor.rowcount > 0

    def add_category(
        self, 
        name: str, 
        color: Optional[str] = None, 
        icon: Optional[str] = None
    ) -> bool:
        """Add a new category.
        
        Args:
            name: Category name
            color: Optional color code
            icon: Optional icon
            
        Returns:
            True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            try:
                cursor = conn.execute("""
                    SELECT MAX(sort_order) FROM categories
                """)
                max_order = cursor.fetchone()[0] or 0
                
                conn.execute("""
                    INSERT INTO categories (name, color, icon, sort_order)
                    VALUES (?, ?, ?, ?)
                """, (name, color, icon, max_order + 1))
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                return False

    def list_categories(self) -> List[Dict]:
        """List all categories.
        
        Returns:
            List of category dictionaries
        """
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute("""
                SELECT * FROM categories 
                ORDER BY sort_order, name
            """)
            return [dict(row) for row in cursor.fetchall()]

    def update_document_tags(self, library_path: str, tags: List[str]) -> bool:
        """Update tags for a document.
        
        Args:
            library_path: Path to document in library
            tags: List of tags
            
        Returns:
            True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE documents 
                SET tags = ?
                WHERE library_path = ?
            """, (json.dumps(tags), library_path))
            conn.commit()
            return cursor.rowcount > 0

    def update_document_notes(self, library_path: str, notes: str) -> bool:
        """Update notes for a document.
        
        Args:
            library_path: Path to document in library
            notes: Notes text
            
        Returns:
            True if successful
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                UPDATE documents 
                SET notes = ?
                WHERE library_path = ?
            """, (notes, library_path))
            conn.commit()
            return cursor.rowcount > 0

    def get_statistics(self) -> Dict:
        """Get database statistics.
        
        Returns:
            Dictionary with statistics
        """
        with sqlite3.connect(self.db_path) as conn:
            stats = {}
            
            cursor = conn.execute("SELECT COUNT(*) FROM documents")
            stats['total_documents'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(*) FROM documents WHERE is_read = TRUE")
            stats['read_documents'] = cursor.fetchone()[0]
            
            cursor = conn.execute("SELECT COUNT(DISTINCT category) FROM documents")
            stats['categories_used'] = cursor.fetchone()[0]
            
            cursor = conn.execute("""
                SELECT category, COUNT(*) as count 
                FROM documents 
                GROUP BY category 
                ORDER BY count DESC
            """)
            stats['documents_by_category'] = [
                {'category': row[0], 'count': row[1]} 
                for row in cursor.fetchall()
            ]
            
            return stats