"""Página de detalle de archivo para ReQperacion."""

import os
import urllib.parse
import reflex as rx
from app.styles.theme import (
    PASTEL_BLUE, PASTEL_BLUE_HOVER, DEEP_SOFT_BLUE, TEXT_PRIMARY, TEXT_SECONDARY,
    WHITE, BORDER_LIGHT, LIGHT_GRAY_BLUE, SOFT_BLUE,
)
from app.components.navbar import navbar
from app.components.file_card import get_file_icon, get_file_color
from app.models import File, ExtractedText, FileTag, User, get_session


# File types that support preview
PREVIEW_IMAGE = {".png", ".jpg", ".jpeg", ".bmp", ".tiff", ".tif", ".webp"}
PREVIEW_PDF = {".pdf"}
PREVIEW_TEXT = {".txt", ".md", ".csv", ".json", ".xml", ".yaml", ".yml", ".log"}
PREVIEW_AUDIO = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".aac", ".wma"}
PREVIEW_VIDEO = {".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm"}


def _get_preview_type_from_filename(filename: str) -> str:
    """Determine the preview type based on file extension (pure Python)."""
    _, ext = os.path.splitext(filename)
    ext = ext.lower()
    if ext in PREVIEW_IMAGE:
        return "image"
    elif ext in PREVIEW_PDF:
        return "pdf"
    elif ext in PREVIEW_TEXT:
        return "text"
    elif ext in PREVIEW_AUDIO:
        return "audio"
    elif ext in PREVIEW_VIDEO:
        return "video"
    return "none"


def _get_preview_url_from_path(file_path: str) -> str:
    """Build the preview URL from a file path (pure Python)."""
    upload_folder = os.environ.get("UPLOAD_FOLDER", "/data/uploads")
    if file_path.startswith(upload_folder):
        relative = file_path[len(upload_folder):].lstrip("/")
        # Use the API URL from config so the frontend can reach the backend
        from reflex.config import get_config
        config = get_config()
        api_url = config.api_url.rstrip("/")
        return f"{api_url}/api/files/{relative}"
    return ""


class FileDetailState(rx.State):
    """State for the file detail page."""
    current_file_id: int = 0
    file_data: dict = {}
    extracted_text: str = ""
    tags: list[str] = []

    @rx.var
    def preview_type(self) -> str:
        """Computed var: preview type based on file extension."""
        filename = self.file_data.get("original_filename", "")
        return _get_preview_type_from_filename(filename)

    @rx.var
    def preview_url(self) -> str:
        """Computed var: URL for file preview."""
        file_path = self.file_data.get("file_path", "")
        return _get_preview_url_from_path(file_path)

    @rx.var
    def download_url(self) -> str:
        """Computed var: full URL for file download."""
        file_path = self.file_data.get("file_path", "")
        return _get_preview_url_from_path(file_path)

    def handle_download(self):
        """Trigger file download via JavaScript."""
        url = self.download_url
        if url:
            filename = self.file_data.get("original_filename", "download")
            # URL-encode filename for query parameter safety
            filename_encoded = urllib.parse.quote(filename, safe="")
            # Escape single quotes for JavaScript string safety
            filename_escaped = filename.replace("'", "\\'")
            # Append download params to force Content-Disposition: attachment
            download_url = f"{url}?download=1&filename={filename_encoded}"
            return rx.call_script(
                f"const a=document.createElement('a');a.href='{download_url}';a.download='{filename_escaped}';document.body.appendChild(a);a.click();document.body.removeChild(a);"
            )

    def load_file(self):
        """Load file details from database using route params."""
        # Get file_id from route params
        file_id = int(self.router.page.params.get("file_id", 0))
        self.current_file_id = file_id

        db = get_session()
        try:
            file_record = db.query(File).filter(File.id == file_id).first()
            if not file_record:
                return rx.redirect("/dashboard")

            # Get the uploader's username
            uploader = db.query(User).filter(User.id == file_record.user_id).first()
            uploader_username = uploader.username if uploader else "?"

            self.file_data = {
                "id": file_record.id,
                "original_filename": file_record.original_filename,
                "stored_filename": file_record.stored_filename,
                "file_type": file_record.file_type,
                "file_size": file_record.file_size,
                "file_size_display": self._format_size(file_record.file_size),
                "description": file_record.description or "",
                "uploaded_at": file_record.uploaded_at.isoformat() if file_record.uploaded_at else "",
                "file_path": file_record.file_path,
                "processing_status": file_record.processing_status,
                "username": uploader_username,
            }

            # Get extracted text
            extracted = (
                db.query(ExtractedText)
                .filter(ExtractedText.file_id == file_id)
                .first()
            )
            self.extracted_text = extracted.content if extracted else ""

            # Get tags
            tag_records = (
                db.query(FileTag)
                .filter(FileTag.file_id == file_id)
                .all()
            )
            self.tags = [t.tag for t in tag_records]

        except Exception as e:
            print(f"Error loading file detail: {e}")
            return rx.redirect("/dashboard")
        finally:
            db.close()

    def _format_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"

    def handle_logout(self):
        """Handle logout."""
        return rx.redirect("/")

    def go_back(self):
        """Go back to dashboard."""
        return rx.redirect("/dashboard")


def preview_panel() -> rx.Component:
    """File preview panel shown on the right side of the detail page."""
    return rx.box(
        rx.vstack(
            # Preview header
            rx.hstack(
                rx.box(
                    width="4px",
                    height="20px",
                    background=f"linear-gradient(180deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER})",
                    border_radius="0 4px 4px 0",
                ),
                rx.text(
                    "Vista previa",
                    font_size="1.1rem",
                    font_weight="700",
                    color=TEXT_PRIMARY,
                ),
                spacing="3",
                align="center",
                width="100%",
                margin_bottom="0.75rem",
            ),
            # Preview content using rx.match for conditional rendering
            rx.match(
                FileDetailState.preview_type,
                # Image preview
                ("image",
                 rx.box(
                     rx.image(
                         src=FileDetailState.preview_url,
                         alt=FileDetailState.file_data.get("original_filename", ""),
                         width="100%",
                         height="auto",
                         max_height="70vh",
                         object_fit="contain",
                         border_radius="10px",
                         box_shadow="0 2px 12px rgba(0, 0, 0, 0.08)",
                     ),
                     width="100%",
                     overflow="hidden",
                 )),
                # PDF preview
                ("pdf",
                 rx.box(
                     rx.el.embed(
                         src=FileDetailState.preview_url,
                         type="application/pdf",
                         width="100%",
                         height="70vh",
                     ),
                     width="100%",
                     border_radius="10px",
                     overflow="hidden",
                     border=f"1px solid {BORDER_LIGHT}",
                     box_shadow="0 2px 12px rgba(0, 0, 0, 0.08)",
                 )),
                # Text preview
                ("text",
                 rx.box(
                     rx.text(
                         FileDetailState.extracted_text,
                         font_size="0.85rem",
                         color=TEXT_SECONDARY,
                         white_space="pre-wrap",
                         line_height="1.7",
                         font_family="'JetBrains Mono', 'Fira Code', monospace",
                     ),
                     width="100%",
                     max_height="70vh",
                     overflow_y="auto",
                     padding="1.25rem",
                     background_color=LIGHT_GRAY_BLUE,
                     border_radius="10px",
                     border=f"1px solid {BORDER_LIGHT}",
                     box_shadow="inset 0 2px 4px rgba(0, 0, 0, 0.04)",
                 )),
                # Audio preview
                ("audio",
                 rx.box(
                     rx.el.audio(
                         src=FileDetailState.preview_url,
                         controls=True,
                         width="100%",
                     ),
                     width="100%",
                     padding="2.5rem 1rem",
                     background_color=LIGHT_GRAY_BLUE,
                     border_radius="10px",
                     text_align="center",
                 )),
                # Video preview
                ("video",
                 rx.box(
                     rx.el.video(
                         src=FileDetailState.preview_url,
                         controls=True,
                         width="100%",
                         max_height="70vh",
                         border_radius="10px",
                     ),
                     width="100%",
                     border_radius="10px",
                     overflow="hidden",
                     box_shadow="0 2px 12px rgba(0, 0, 0, 0.08)",
                 )),
                # No preview available (default)
                rx.box(
                    rx.vstack(
                        rx.box(
                            rx.icon(
                                tag=get_file_icon(
                                    FileDetailState.file_data.get("file_type", "other")
                                ),
                                color=PASTEL_BLUE,
                                font_size="3.5rem",
                            ),
                            padding="1rem",
                            background_color=LIGHT_GRAY_BLUE,
                            border_radius="16px",
                        ),
                        rx.text(
                            "Vista previa no disponible",
                            font_size="1rem",
                            color=TEXT_SECONDARY,
                            font_weight="600",
                        ),
                        rx.text(
                            "Este tipo de archivo no se puede previsualizar.",
                            font_size="0.85rem",
                            color=TEXT_SECONDARY,
                        ),
                        spacing="3",
                        align="center",
                        width="100%",
                    ),
                    padding="3rem 1rem",
                    background_color=LIGHT_GRAY_BLUE,
                    border_radius="10px",
                    border=f"1px dashed {BORDER_LIGHT}",
                    width="100%",
                ),
            ),
            spacing="3",
            width="100%",
        ),
        background_color="rgba(255, 255, 255, 0.92)",
        backdrop_filter="blur(12px)",
        border="1px solid rgba(255, 255, 255, 0.3)",
        border_radius="16px",
        padding="1.5rem",
        width="100%",
        box_shadow="0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.06)",
        position="sticky",
        top="1rem",
    )


def file_detail_page() -> rx.Component:
    """File detail view page with two-column layout."""
    return rx.box(
        navbar(on_logout=FileDetailState.handle_logout),
        rx.box(
            # Back button
            rx.button(
                rx.hstack(
                    rx.icon(tag="arrow-left", font_size="0.9rem"),
                    rx.text("Volver a archivos", font_size="0.9rem"),
                    spacing="2",
                ),
                on_click=FileDetailState.go_back,
                variant="ghost",
                color=TEXT_SECONDARY,
                border_radius="8px",
                padding="0.4rem 0.75rem",
                _hover={"color": TEXT_PRIMARY, "background_color": "rgba(126, 200, 227, 0.1)"},
                margin_bottom="1rem",
            ),
            # Two-column layout
            rx.flex(
                # Left column: File info
                rx.box(
                    rx.vstack(
                        # File header
                        rx.hstack(
                            # File icon
                            rx.box(
                                rx.icon(
                                    tag=get_file_icon(
                                        FileDetailState.file_data.get("file_type", "other")
                                    ),
                                    color=PASTEL_BLUE,
                                    font_size="2rem",
                                ),
                                background=f"linear-gradient(135deg, {LIGHT_GRAY_BLUE}, {WHITE})",
                                border_radius="14px",
                                padding="1.25rem",
                                border=f"1px solid {BORDER_LIGHT}",
                            ),
                            rx.vstack(
                                rx.text(
                                    FileDetailState.file_data.get("original_filename", ""),
                                    font_size="1.5rem",
                                    font_weight="700",
                                    color=TEXT_PRIMARY,
                                    letter_spacing="-0.3px",
                                ),
                                rx.hstack(
                                    rx.box(
                                        FileDetailState.file_data.get("file_type", "other"),
                                        font_size="0.8rem",
                                        font_weight="600",
                                        color=TEXT_PRIMARY,
                                        background_color=get_file_color(
                                            FileDetailState.file_data.get("file_type", "other")
                                        ),
                                        padding="0.2rem 0.6rem",
                                        border_radius="4px",
                                    ),
                                    rx.text(
                                        FileDetailState.file_data.get("file_size_display", ""),
                                        font_size="0.85rem",
                                        color=TEXT_SECONDARY,
                                    ),
                                    rx.text(
                                        FileDetailState.file_data.get("uploaded_at", ""),
                                        font_size="0.85rem",
                                        color=TEXT_SECONDARY,
                                    ),
                                    # Username (visible when exploring)
                                    rx.cond(
                                        FileDetailState.file_data.get("username", "") != "",
                                        rx.hstack(
                                            rx.icon(tag="user", font_size="0.75rem", color=DEEP_SOFT_BLUE),
                                            rx.text(
                                                FileDetailState.file_data.get("username", ""),
                                                font_size="0.85rem",
                                                color=DEEP_SOFT_BLUE,
                                                font_weight="500",
                                            ),
                                            spacing="1",
                                            align="center",
                                        ),
                                    ),
                                    spacing="3",
                                    align="center",
                                    flex_wrap="wrap",
                                ),
                                spacing="1",
                            ),
                            rx.spacer(),
                            # Download button
                            rx.button(
                                rx.hstack(
                                    rx.icon(tag="download", font_size="1rem"),
                                    rx.text("Descargar", font_size="0.9rem"),
                                    spacing="2",
                                ),
                                on_click=FileDetailState.handle_download,
                                background=f"linear-gradient(135deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER})",
                                color=TEXT_PRIMARY,
                                font_weight="600",
                                border="none",
                                border_radius="10px",
                                padding="0.6rem 1.25rem",
                                cursor="pointer",
                                transition="all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
                                box_shadow=f"0 4px 14px rgba(126, 200, 227, 0.35)",
                                _hover={
                                    "transform": "translateY(-2px)",
                                    "box_shadow": f"0 6px 20px rgba(126, 200, 227, 0.5)",
                                },
                            ),
                            width="100%",
                            align="center",
                            spacing="4",
                        ),
                        # Description
                        rx.cond(
                            FileDetailState.file_data.get("description", ""),
                            rx.box(
                                rx.text(
                                    "Descripción",
                                    font_size="0.9rem",
                                    font_weight="600",
                                    color=TEXT_PRIMARY,
                                    margin_bottom="0.5rem",
                                ),
                                rx.text(
                                    FileDetailState.file_data.get("description", ""),
                                    font_size="0.95rem",
                                    color=TEXT_SECONDARY,
                                    line_height="1.7",
                                ),
                                width="100%",
                                padding="1.25rem",
                                background_color=LIGHT_GRAY_BLUE,
                                border_radius="10px",
                                border=f"1px solid {BORDER_LIGHT}",
                            ),
                        ),
                        # Tags
                        rx.cond(
                            FileDetailState.tags.length() > 0,
                            rx.box(
                                rx.text(
                                    "Etiquetas",
                                    font_size="0.9rem",
                                    font_weight="600",
                                    color=TEXT_PRIMARY,
                                    margin_bottom="0.5rem",
                                ),
                                rx.flex(
                                    rx.foreach(
                                        FileDetailState.tags,
                                        lambda tag: rx.box(
                                            tag,
                                            font_size="0.8rem",
                                            color=TEXT_PRIMARY,
                                            background_color=SOFT_BLUE,
                                            padding="0.25rem 0.75rem",
                                            border_radius="20px",
                                            font_weight="500",
                                            border=f"1px solid rgba(184, 212, 232, 0.5)",
                                        ),
                                    ),
                                    spacing="2",
                                    flex_wrap="wrap",
                                ),
                                width="100%",
                            ),
                        ),
                        # Extracted text
                        rx.cond(
                            FileDetailState.extracted_text,
                            rx.box(
                                rx.text(
                                    "Contenido extraído",
                                    font_size="0.9rem",
                                    font_weight="600",
                                    color=TEXT_PRIMARY,
                                    margin_bottom="0.5rem",
                                ),
                                rx.box(
                                    rx.text(
                                        FileDetailState.extracted_text,
                                        font_size="0.85rem",
                                        color=TEXT_SECONDARY,
                                        white_space="pre-wrap",
                                        line_height="1.7",
                                    ),
                                    max_height="400px",
                                    overflow_y="auto",
                                    padding="1.25rem",
                                    background_color=LIGHT_GRAY_BLUE,
                                    border_radius="10px",
                                    border=f"1px solid {BORDER_LIGHT}",
                                    box_shadow="inset 0 2px 4px rgba(0, 0, 0, 0.04)",
                                ),
                                width="100%",
                            ),
                        ),
                        spacing="5",
                        width="100%",
                    ),
                    background_color="rgba(255, 255, 255, 0.92)",
                    backdrop_filter="blur(12px)",
                    border="1px solid rgba(255, 255, 255, 0.3)",
                    border_radius="16px",
                    padding="2rem",
                    width="100%",
                    box_shadow="0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.06)",
                ),
                # Right column: Preview
                rx.box(
                    preview_panel(),
                    width="100%",
                ),
                width="100%",
                gap="1.5rem",
                flex_direction=["column", "column", "row", "row"],
            ),
            width="100%",
            max_width="1200px",
            padding="2rem",
            margin="0 auto",
        ),
        background_color=LIGHT_GRAY_BLUE,
        min_height="100vh",
        width="100%",
    )
