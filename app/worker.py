"""
ReQperacion Background Processing Worker.

This is a standalone script that runs in a separate Docker container.
It polls the database for files with processing_status='pending',
processes them (OCR, Whisper, document extraction), and updates
the status to 'completed' or 'failed'.

This architecture ensures that heavy processing (especially Whisper
model loading + transcription) never blocks the main Reflex app.
"""

import os
import sys
import time
import logging
import signal

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.models import File, ExtractedText, FileTag, get_session
from app.processor import extract_text
from app.ocr import extract_text_from_image, is_image_file
from app.audio_processor import process_audio, process_video, is_audio_file, is_video_file
from app.tags import generate_tags

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [WORKER] %(levelname)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Polling interval in seconds
POLL_INTERVAL = 5

# Shutdown flag
_shutdown = False


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    global _shutdown
    logger.info(f"Received signal {signum}, shutting down gracefully...")
    _shutdown = True


def process_file(file_record: File) -> None:
    """
    Process a single file: extract text, generate tags.
    Updates the file's processing_status on success or failure.
    """
    file_id = file_record.id
    filename = file_record.original_filename
    file_path = file_record.file_path

    logger.info(f"Processing file: {filename} (ID: {file_id})")

    # Mark as processing
    db = get_session()
    try:
        file_rec = db.query(File).filter(File.id == file_id).first()
        if file_rec:
            file_rec.processing_status = "processing"
            db.commit()
    except Exception as e:
        logger.error(f"Failed to set processing status for {filename}: {e}")
        db.rollback()
    finally:
        db.close()

    # Extract text based on file type
    extracted_text = ""
    try:
        if is_image_file(filename):
            logger.info(f"Running OCR on {filename}")
            extracted_text = extract_text_from_image(file_path)
        elif is_audio_file(filename):
            logger.info(f"Transcribing audio: {filename}")
            extracted_text = process_audio(file_path)
        elif is_video_file(filename):
            logger.info(f"Transcribing video: {filename}")
            extracted_text = process_video(file_path)
        else:
            logger.info(f"Extracting text from {filename}")
            extracted_text = extract_text(file_path)

        logger.info(f"Extracted {len(extracted_text)} characters from {filename}")
    except Exception as e:
        logger.error(f"Processing failed for {filename}: {e}")
        extracted_text = ""

    # Store results in DB
    db = get_session()
    try:
        file_rec = db.query(File).filter(File.id == file_id).first()
        if not file_rec:
            logger.warning(f"File {file_id} not found in DB, skipping")
            return

        if extracted_text.strip():
            # Save extracted text
            text_record = ExtractedText(
                file_id=file_id,
                content=extracted_text,
            )
            db.add(text_record)

            # Generate and save tags
            tags = generate_tags(extracted_text)
            for tag in tags:
                tag_record = FileTag(
                    file_id=file_id,
                    tag=tag,
                )
                db.add(tag_record)

            file_rec.processing_status = "completed"
            logger.info(
                f"Processing complete for {filename}: "
                f"{len(extracted_text)} chars, {len(tags)} tags"
            )
        else:
            # No text extracted — still mark as completed (nothing to index)
            file_rec.processing_status = "completed"
            logger.info(f"Processing complete for {filename}: no text extracted")

        db.commit()
    except Exception as e:
        db.rollback()
        logger.error(f"DB update failed for {filename}: {e}")
        # Mark as failed
        try:
            file_rec = db.query(File).filter(File.id == file_id).first()
            if file_rec:
                file_rec.processing_status = "failed"
                db.commit()
        except Exception:
            db.rollback()
    finally:
        db.close()


def main():
    """Main worker loop: poll for pending files and process them."""
    logger.info("ReQperacion Worker started")
    logger.info(f"Polling interval: {POLL_INTERVAL}s")
    logger.info("Waiting for pending files...")

    # Register signal handlers for graceful shutdown
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    while not _shutdown:
        try:
            db = get_session()
            try:
                # Find all pending files, ordered by upload time (oldest first)
                pending_files = (
                    db.query(File)
                    .filter(File.processing_status == "pending")
                    .order_by(File.uploaded_at.asc())
                    .all()
                )

                if pending_files:
                    logger.info(f"Found {len(pending_files)} pending file(s)")
                    for file_record in pending_files:
                        if _shutdown:
                            break
                        process_file(file_record)
                else:
                    # No pending files, just wait
                    pass

            except Exception as e:
                logger.error(f"Database query error: {e}")
            finally:
                db.close()

        except Exception as e:
            logger.error(f"Worker loop error: {e}")

        # Wait before next poll (check shutdown every second)
        for _ in range(POLL_INTERVAL):
            if _shutdown:
                break
            time.sleep(1)

    logger.info("Worker shutdown complete")


if __name__ == "__main__":
    main()
