"""File upload handler for ReQperacion.

Handles saving uploaded files to disk and creating the database record.
File processing (OCR, Whisper, document extraction) is handled by a
separate worker container that polls for pending files.

Architecture:
  1. Save file to disk + create DB record with status="pending" (fast)
  2. Return success to the user immediately
  3. Worker container picks up pending files and processes them
  4. Worker updates DB with extracted text + tags when done
"""

import os
import uuid
import logging
from datetime import datetime

from app.models import File, get_session

logger = logging.getLogger(__name__)

# Maximum file size: 50MB
MAX_FILE_SIZE = 50 * 1024 * 1024


def get_upload_folder() -> str:
    """Get the upload folder path from environment or default."""
    return os.getenv("UPLOAD_FOLDER", "/data/uploads")


def can_process(filename: str) -> bool:
    """Check if a file extension supports text extraction."""
    from app.audio_processor import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS
    from app.ocr import IMAGE_EXTENSIONS

    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    # All processable extensions
    processable = {
        # Documents
        ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".txt", ".csv",
        ".md", ".json", ".xml", ".html", ".htm",
        # Code files
        ".py", ".js", ".ts", ".css", ".sql",
    }
    processable.update(IMAGE_EXTENSIONS)
    processable.update(AUDIO_EXTENSIONS)
    processable.update(VIDEO_EXTENSIONS)

    return ext in processable


def get_file_type(filename: str) -> str:
    """Categorize a file by its extension."""
    from app.audio_processor import AUDIO_EXTENSIONS, VIDEO_EXTENSIONS
    from app.ocr import IMAGE_EXTENSIONS

    _, ext = os.path.splitext(filename)
    ext = ext.lower()

    doc_exts = {".pdf", ".doc", ".docx"}
    spreadsheet_exts = {".xls", ".xlsx", ".csv"}
    text_exts = {".txt", ".md", ".json", ".xml", ".html", ".htm"}
    code_exts = {".py", ".js", ".ts", ".css", ".sql"}

    if ext in IMAGE_EXTENSIONS:
        return "image"
    elif ext in doc_exts:
        return "document"
    elif ext in spreadsheet_exts:
        return "spreadsheet"
    elif ext in text_exts:
        return "text"
    elif ext in code_exts:
        return "code"
    elif ext in AUDIO_EXTENSIONS:
        return "audio"
    elif ext in VIDEO_EXTENSIONS:
        return "video"
    else:
        return "other"


def handle_upload(
    user_id: int,
    file_data: bytes,
    original_filename: str,
    description: str = "",
) -> tuple[bool, str, dict | None]:
    """
    Handle a file upload: save to disk, create DB record with status='pending'.
    
    File processing is done asynchronously by the worker container.
    This function is fast and never blocks on processing.
    
    Args:
        user_id: The uploading user's ID
        file_data: Raw file bytes
        original_filename: Original filename from the upload
        description: Optional user-provided description
    
    Returns:
        (success: bool, message: str, file_info: dict | None)
    """
    # Validate file
    if not original_filename:
        return False, "No se ha seleccionado ningún archivo.", None

    if len(file_data) > MAX_FILE_SIZE:
        return False, "El archivo es demasiado grande. El tamaño máximo es 50 MB.", None

    if len(file_data) == 0:
        return False, "El archivo está vacío.", None

    # Generate unique stored filename
    _, ext = os.path.splitext(original_filename)
    stored_filename = f"{uuid.uuid4().hex}{ext}"
    file_type = get_file_type(original_filename)

    # Ensure upload directory exists
    upload_folder = get_upload_folder()
    user_folder = os.path.join(upload_folder, str(user_id))
    os.makedirs(user_folder, exist_ok=True)

    # Save file to disk
    file_path = os.path.join(user_folder, stored_filename)
    try:
        with open(file_path, "wb") as f:
            f.write(file_data)
    except Exception as e:
        logger.error(f"Failed to save file: {e}")
        return False, f"Error al guardar el archivo: {str(e)}", None

    # Store in database with status="pending"
    db = get_session()
    try:
        file_record = File(
            user_id=user_id,
            original_filename=original_filename,
            stored_filename=stored_filename,
            file_path=file_path,
            file_type=file_type,
            file_size=len(file_data),
            description=description,
            uploaded_at=datetime.utcnow(),
            processing_status="pending",
        )
        db.add(file_record)
        db.flush()

        file_id = file_record.id
        db.commit()

        file_info = {
            "id": file_id,
            "original_filename": file_record.original_filename,
            "file_type": file_record.file_type,
            "file_size": file_record.file_size,
            "file_size_display": _format_size(file_record.file_size),
            "description": file_record.description or "",
            "uploaded_at": file_record.uploaded_at.isoformat() if file_record.uploaded_at else "",
            "stored_filename": file_record.stored_filename,
            "processing_status": "pending",
        }

        logger.info(f"File saved: {original_filename} (ID: {file_id}) — pending processing")
        return True, "¡Archivo subido correctamente! El procesamiento comenzará en breve.", file_info

    except Exception as e:
        db.rollback()
        logger.error(f"Database error during upload: {e}")
        # Clean up the saved file
        try:
            os.remove(file_path)
        except OSError:
            pass
        return False, f"Error al subir el archivo: {str(e)}", None
    finally:
        db.close()


def _format_size(size_bytes: int) -> str:
    """Format file size in human-readable format."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
