"""
Photo Service for Mobile Crew Interface
Handles photo uploads for tasks - crew members can attach photos with GPS.

AgTools v2.6.0 Phase 6.5
"""

import os
import sqlite3
import uuid
import shutil
from datetime import datetime
from typing import Optional, List, Tuple, Dict, Any
from pathlib import Path

from pydantic import BaseModel, Field


# ============================================================================
# CONFIGURATION
# ============================================================================

# Base directory for uploads (relative to backend/)
UPLOADS_DIR = "uploads"
PHOTOS_SUBDIR = "photos"

# Allowed file extensions
ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.heic', '.heif'}

# Max file size in bytes (10 MB)
MAX_FILE_SIZE = 10 * 1024 * 1024


# ============================================================================
# PYDANTIC MODELS
# ============================================================================

class PhotoResponse(BaseModel):
    """Photo response model"""
    id: int
    task_id: int
    user_id: int
    user_name: Optional[str] = None
    filename: str
    original_filename: str
    file_path: str
    file_size: int
    mime_type: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    caption: Optional[str] = None
    created_at: datetime


class PhotoUploadResult(BaseModel):
    """Result of photo upload"""
    success: bool
    photo: Optional[PhotoResponse] = None
    error: Optional[str] = None


# ============================================================================
# PHOTO SERVICE CLASS
# ============================================================================

class PhotoService:
    """
    Service for managing task photos:
    - Upload and store photos
    - Associate photos with tasks
    - Store GPS coordinates
    - List photos for tasks
    - Delete photos
    """

    def __init__(self, db_path: str = "agtools.db", uploads_base: Optional[str] = None):
        """
        Initialize photo service.

        Args:
            db_path: Path to SQLite database
            uploads_base: Base directory for uploads (defaults to backend/uploads)
        """
        self.db_path = db_path

        # Set up uploads directory
        if uploads_base:
            self.uploads_base = Path(uploads_base)
        else:
            # Default to backend/uploads
            backend_dir = Path(__file__).parent.parent
            self.uploads_base = backend_dir / UPLOADS_DIR

        self.photos_dir = self.uploads_base / PHOTOS_SUBDIR

        # Ensure directories exist
        self._ensure_directories()
        self._init_database()

    def _ensure_directories(self) -> None:
        """Create upload directories if they don't exist."""
        self.uploads_base.mkdir(parents=True, exist_ok=True)
        self.photos_dir.mkdir(parents=True, exist_ok=True)

        # Create a .gitkeep file
        gitkeep = self.uploads_base / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()

    def _get_connection(self) -> sqlite3.Connection:
        """Get a database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_database(self) -> None:
        """Initialize database tables if they don't exist."""
        conn = self._get_connection()
        cursor = conn.cursor()

        # Create task_photos table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS task_photos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                filename VARCHAR(255) NOT NULL,
                original_filename VARCHAR(255) NOT NULL,
                file_path VARCHAR(500) NOT NULL,
                file_size INTEGER NOT NULL,
                mime_type VARCHAR(100) NOT NULL,
                latitude REAL,
                longitude REAL,
                caption TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)

        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_photos_task ON task_photos(task_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_task_photos_user ON task_photos(user_id)")

        conn.commit()
        conn.close()

    # ========================================================================
    # HELPER METHODS
    # ========================================================================

    def _row_to_response(self, row: sqlite3.Row) -> PhotoResponse:
        """Convert a database row to PhotoResponse."""
        return PhotoResponse(
            id=row["id"],
            task_id=row["task_id"],
            user_id=row["user_id"],
            user_name=row.get("user_name"),
            filename=row["filename"],
            original_filename=row["original_filename"],
            file_path=row["file_path"],
            file_size=row["file_size"],
            mime_type=row["mime_type"],
            latitude=row["latitude"],
            longitude=row["longitude"],
            caption=row["caption"],
            created_at=row["created_at"]
        )

    def _get_mime_type(self, extension: str) -> str:
        """Get MIME type from file extension."""
        mime_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.gif': 'image/gif',
            '.webp': 'image/webp',
            '.heic': 'image/heic',
            '.heif': 'image/heif',
        }
        return mime_types.get(extension.lower(), 'application/octet-stream')

    def _generate_filename(self, original_filename: str, task_id: int) -> str:
        """Generate a unique filename for storage."""
        ext = Path(original_filename).suffix.lower()
        unique_id = uuid.uuid4().hex[:12]
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"task_{task_id}_{timestamp}_{unique_id}{ext}"

    def _validate_file(self, filename: str, file_size: int) -> Tuple[bool, Optional[str]]:
        """
        Validate file for upload.

        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check extension
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            allowed = ', '.join(ALLOWED_EXTENSIONS)
            return False, f"File type not allowed. Allowed types: {allowed}"

        # Check size
        if file_size > MAX_FILE_SIZE:
            max_mb = MAX_FILE_SIZE / (1024 * 1024)
            return False, f"File too large. Maximum size: {max_mb:.0f} MB"

        return True, None

    # ========================================================================
    # CRUD METHODS
    # ========================================================================

    async def save_photo(
        self,
        task_id: int,
        user_id: int,
        file_content: bytes,
        original_filename: str,
        latitude: Optional[float] = None,
        longitude: Optional[float] = None,
        caption: Optional[str] = None
    ) -> PhotoUploadResult:
        """
        Save an uploaded photo.

        Args:
            task_id: Task ID to attach photo to
            user_id: User ID of uploader
            file_content: Binary file content
            original_filename: Original filename from upload
            latitude: GPS latitude (optional)
            longitude: GPS longitude (optional)
            caption: Photo caption (optional)

        Returns:
            PhotoUploadResult with success status and photo data
        """
        file_size = len(file_content)

        # Validate file
        is_valid, error = self._validate_file(original_filename, file_size)
        if not is_valid:
            return PhotoUploadResult(success=False, error=error)

        # Verify task exists
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM tasks WHERE id = ? AND is_active = 1", (task_id,))
        if not cursor.fetchone():
            conn.close()
            return PhotoUploadResult(success=False, error="Task not found")

        # Generate unique filename
        new_filename = self._generate_filename(original_filename, task_id)
        file_path = self.photos_dir / new_filename
        relative_path = f"{PHOTOS_SUBDIR}/{new_filename}"

        # Get MIME type
        ext = Path(original_filename).suffix.lower()
        mime_type = self._get_mime_type(ext)

        try:
            # Save file to disk
            with open(file_path, 'wb') as f:
                f.write(file_content)

            # Save to database
            cursor.execute("""
                INSERT INTO task_photos (
                    task_id, user_id, filename, original_filename,
                    file_path, file_size, mime_type, latitude, longitude, caption
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task_id,
                user_id,
                new_filename,
                original_filename,
                relative_path,
                file_size,
                mime_type,
                latitude,
                longitude,
                caption
            ))

            photo_id = cursor.lastrowid
            conn.commit()
            conn.close()

            # Get the saved photo
            photo = self.get_photo_by_id(photo_id)
            return PhotoUploadResult(success=True, photo=photo)

        except Exception as e:
            # Clean up file if database insert failed
            if file_path.exists():
                file_path.unlink()
            conn.close()
            return PhotoUploadResult(success=False, error=str(e))

    def get_photo_by_id(self, photo_id: int) -> Optional[PhotoResponse]:
        """Get photo by ID with joined user name."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.id, p.task_id, p.user_id, p.filename, p.original_filename,
                p.file_path, p.file_size, p.mime_type,
                p.latitude, p.longitude, p.caption, p.created_at,
                u.first_name || ' ' || u.last_name as user_name
            FROM task_photos p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.id = ?
        """, (photo_id,))

        row = cursor.fetchone()
        conn.close()

        if not row:
            return None

        return self._row_to_response(row)

    def list_photos_for_task(self, task_id: int) -> List[PhotoResponse]:
        """Get all photos for a task."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                p.id, p.task_id, p.user_id, p.filename, p.original_filename,
                p.file_path, p.file_size, p.mime_type,
                p.latitude, p.longitude, p.caption, p.created_at,
                u.first_name || ' ' || u.last_name as user_name
            FROM task_photos p
            LEFT JOIN users u ON p.user_id = u.id
            WHERE p.task_id = ?
            ORDER BY p.created_at DESC
        """, (task_id,))

        rows = cursor.fetchall()
        conn.close()

        return [self._row_to_response(row) for row in rows]

    def delete_photo(
        self,
        photo_id: int,
        user_id: int,
        is_admin: bool = False
    ) -> Tuple[bool, Optional[str]]:
        """
        Delete a photo.
        Users can delete their own photos, admins can delete any.

        Args:
            photo_id: Photo ID to delete
            user_id: User requesting deletion
            is_admin: Whether user is admin

        Returns:
            Tuple of (success, error_message)
        """
        conn = self._get_connection()
        cursor = conn.cursor()

        # Get photo info
        cursor.execute(
            "SELECT user_id, filename FROM task_photos WHERE id = ?",
            (photo_id,)
        )
        row = cursor.fetchone()

        if not row:
            conn.close()
            return False, "Photo not found"

        # Check permission
        if row["user_id"] != user_id and not is_admin:
            conn.close()
            return False, "Can only delete your own photos"

        # Delete file from disk
        file_path = self.photos_dir / row["filename"]
        try:
            if file_path.exists():
                file_path.unlink()
        except Exception as e:
            # Log but don't fail - orphan files are less bad than orphan records
            print(f"Warning: Could not delete file {file_path}: {e}")

        # Delete from database
        cursor.execute("DELETE FROM task_photos WHERE id = ?", (photo_id,))
        conn.commit()
        conn.close()

        return True, None

    def get_photo_count_for_task(self, task_id: int) -> int:
        """Get count of photos for a task."""
        conn = self._get_connection()
        cursor = conn.cursor()

        cursor.execute(
            "SELECT COUNT(*) as count FROM task_photos WHERE task_id = ?",
            (task_id,)
        )
        row = cursor.fetchone()
        conn.close()

        return row["count"] if row else 0

    def get_file_path(self, filename: str) -> Optional[Path]:
        """Get full file path for a photo filename."""
        file_path = self.photos_dir / filename
        if file_path.exists():
            return file_path
        return None


# ============================================================================
# SINGLETON INSTANCE
# ============================================================================

_photo_service: Optional[PhotoService] = None


def get_photo_service(db_path: str = "agtools.db") -> PhotoService:
    """Get or create the photo service singleton."""
    global _photo_service

    if _photo_service is None:
        _photo_service = PhotoService(db_path)

    return _photo_service
