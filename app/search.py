"""Search module for ReQperacion.

Implements weighted full-text search across filenames, descriptions,
extracted text content, and tags using MySQL FULLTEXT indexes.

Relevance weights:
- Filename: 10x
- Description: 5x
- Extracted text: 3x
- Tags: 2x
"""

import logging
from sqlalchemy import text
from app.models import get_session

logger = logging.getLogger(__name__)


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


def search_files(user_id: int, query: str) -> list[dict]:
    """
    Search files belonging to a user with weighted relevance scoring.
    
    Args:
        user_id: The user's ID
        query: The search query string
    
    Returns:
        List of dicts with file info and relevance score, sorted by relevance
    """
    if not query or not query.strip():
        return []

    # Sanitize the query for MySQL FULLTEXT search
    # Escape special characters and add wildcard for partial matching
    clean_query = _sanitize_query(query)

    if not clean_query:
        return []

    db = get_session()
    try:
        sql = text("""
            SELECT DISTINCT
                f.id,
                f.original_filename,
                f.file_type,
                f.file_size,
                f.description,
                f.uploaded_at,
                f.stored_filename,
                f.processing_status,
                (
                    (MATCH(f.original_filename) AGAINST(:query IN BOOLEAN MODE) * 10.0)
                    + COALESCE(
                        (MATCH(f.description) AGAINST(:query IN BOOLEAN MODE) * 5.0),
                        0
                    )
                    + COALESCE(
                        (SELECT MATCH(et.content) AGAINST(:query IN BOOLEAN MODE) * 3.0
                         FROM extracted_texts et
                         WHERE et.file_id = f.id
                         LIMIT 1),
                        0
                    )
                    + COALESCE(
                        (SELECT MATCH(ft.tag) AGAINST(:query IN BOOLEAN MODE) * 2.0
                         FROM file_tags ft
                         WHERE ft.file_id = f.id
                         LIMIT 1),
                        0
                    )
                ) AS relevance_score
            FROM files f
            LEFT JOIN extracted_texts et ON et.file_id = f.id
            LEFT JOIN file_tags ft ON ft.file_id = f.id
            WHERE f.user_id = :user_id
                AND (
                    MATCH(f.original_filename) AGAINST(:query IN BOOLEAN MODE)
                    OR MATCH(f.description) AGAINST(:query IN BOOLEAN MODE)
                    OR MATCH(et.content) AGAINST(:query IN BOOLEAN MODE)
                    OR MATCH(ft.tag) AGAINST(:query IN BOOLEAN MODE)
                )
            ORDER BY relevance_score DESC
            LIMIT 50
        """)

        result = db.execute(sql, {
            "user_id": user_id,
            "query": clean_query,
        })

        files = []
        for row in result:
            file_size = row[3]
            files.append({
                "id": row[0],
                "original_filename": row[1],
                "file_type": row[2],
                "file_size": file_size,
                "file_size_display": _format_size(file_size) if file_size else "0 B",
                "description": row[4],
                "uploaded_at": row[5].isoformat() if row[5] else None,
                "stored_filename": row[6],
                "processing_status": row[7] or "pending",
                "relevance_score": round(float(row[8]), 2) if row[8] else 0,
            })

        return files

    except Exception as e:
        logger.error(f"Search error: {e}")
        # Fallback: simple LIKE search if FULLTEXT fails
        return _fallback_search(db, user_id, query)
    finally:
        db.close()


def _sanitize_query(query: str) -> str:
    """
    Sanitize and prepare a query for MySQL BOOLEAN MODE search.
    Adds wildcards for partial matching.
    """
    # Remove special MySQL FULLTEXT characters
    special_chars = r'+-><()~*""'
    for char in special_chars:
        query = query.replace(char, " ")

    # Split into words, filter empty, add wildcard
    words = [w.strip() for w in query.split() if w.strip()]
    if not words:
        return ""

    # Add wildcard to each word for partial matching
    # Also add + (must have) for better precision
    return " ".join(f"+{word}*" for word in words)


def _fallback_search(db, user_id: int, query: str) -> list[dict]:
    """
    Fallback search using LIKE when FULLTEXT is not available.
    """
    like_pattern = f"%{query}%"
    try:
        sql = text("""
            SELECT DISTINCT
                f.id,
                f.original_filename,
                f.file_type,
                f.file_size,
                f.description,
                f.uploaded_at,
                f.stored_filename,
                f.processing_status,
                1.0 AS relevance_score
            FROM files f
            LEFT JOIN extracted_texts et ON et.file_id = f.id
            LEFT JOIN file_tags ft ON ft.file_id = f.id
            WHERE f.user_id = :user_id
                AND (
                    f.original_filename LIKE :pattern
                    OR f.description LIKE :pattern
                    OR et.content LIKE :pattern
                    OR ft.tag LIKE :pattern
                )
            ORDER BY
                CASE
                    WHEN f.original_filename LIKE :pattern THEN 10
                    WHEN f.description LIKE :pattern THEN 5
                    WHEN et.content LIKE :pattern THEN 3
                    WHEN ft.tag LIKE :pattern THEN 2
                    ELSE 1
                END DESC
            LIMIT 50
        """)

        result = db.execute(sql, {
            "user_id": user_id,
            "pattern": like_pattern,
        })

        files = []
        for row in result:
            file_size = row[3]
            files.append({
                "id": row[0],
                "original_filename": row[1],
                "file_type": row[2],
                "file_size": file_size,
                "file_size_display": _format_size(file_size) if file_size else "0 B",
                "description": row[4],
                "uploaded_at": row[5].isoformat() if row[5] else None,
                "stored_filename": row[6],
                "processing_status": row[7] or "pending",
                "relevance_score": float(row[8]),
            })

        return files

    except Exception as e:
        logger.error(f"Fallback search error: {e}")
        return []
