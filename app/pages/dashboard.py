"""Página principal de ReQperacion - vista de listado de archivos."""

import os
import asyncio
import reflex as rx
from app.styles.theme import (
    PASTEL_BLUE, PASTEL_BLUE_HOVER, DEEP_SOFT_BLUE, TEXT_PRIMARY, TEXT_SECONDARY,
    WHITE, BORDER_LIGHT, LIGHT_GRAY_BLUE, pastel_blue_input, section_title,
)
from app.components.navbar import navbar
from app.components.file_card import file_card
from app.components.search_bar import search_bar
from app.models import File, ExtractedText, FileTag, get_session
from app.search import search_files


def format_file_size_py(size_bytes: int) -> str:
    """Format file size in human-readable format (pure Python)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


class DashboardState(rx.State):
    """State for the dashboard page."""
    files: list[dict] = []
    search_query: str = ""
    is_searching: bool = False
    show_upload_modal: bool = False
    upload_description: str = ""
    upload_error: str = ""
    upload_success: str = ""
    is_uploading: bool = False
    selected_file: dict | None = None
    upload_filename: str = ""
    # Stored upload data (file bytes + original name) for two-step upload
    _pending_upload_data: bytes = b""
    _pending_upload_name: str = ""
    # Auto-refresh counter for checking processing status
    _refresh_tick: int = 0
    # Change password modal
    show_change_password_modal: bool = False
    cp_old_password: str = ""
    cp_new_password: str = ""
    cp_confirm_password: str = ""
    cp_error: str = ""
    cp_success: str = ""

    async def load_user_files(self):
        """Load files for the current user."""
        from app.app import AppState
        app_state = await self.get_state(AppState)
        uid = app_state.user_id
        if not uid:
            return rx.redirect("/")

        db = get_session()
        try:
            user_files = (
                db.query(File)
                .filter(File.user_id == uid)
                .order_by(File.uploaded_at.desc())
                .all()
            )
            self.files = [
                {
                    "id": f.id,
                    "original_filename": f.original_filename,
                    "file_type": f.file_type,
                    "file_size": f.file_size,
                    "file_size_display": format_file_size_py(f.file_size),
                    "description": f.description or "",
                    "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else "",
                    "stored_filename": f.stored_filename,
                    "processing_status": f.processing_status or "pending",
                }
                for f in user_files
            ]
        except Exception as e:
            print(f"Error loading files: {e}")
            self.files = []
        finally:
            db.close()

        # Start the auto-refresh tick cycle after loading files
        return rx.call_script(
            "setTimeout(() => null, 5000)",
            callback=DashboardState.tick,
        )

    async def handle_search(self):
        """Execute search when user presses Enter."""
        if not self.search_query.strip():
            await self.load_user_files()
            return

        from app.app import AppState
        app_state = await self.get_state(AppState)
        uid = app_state.user_id

        self.is_searching = True
        try:
            results = search_files(uid, self.search_query)
            self.files = results
        except Exception as e:
            print(f"Search error: {e}")
        finally:
            self.is_searching = False

    def set_search_query(self, value: str):
        """Update search query."""
        self.search_query = value

    def set_upload_description(self, value: str):
        """Set the upload description."""
        self.upload_description = value

    def open_upload_modal(self):
        """Open the upload modal."""
        self.show_upload_modal = True
        self.upload_filename = ""
        self.upload_description = ""
        self.upload_error = ""
        self.upload_success = ""
        self._pending_upload_data = b""
        self._pending_upload_name = ""

    def close_upload_modal(self):
        """Close the upload modal."""
        self.show_upload_modal = False

    def handle_file_selected(self, files: list[rx.UploadFile]):
        """Store selected file info (called from on_drop) without uploading yet."""
        self.upload_error = ""
        self.upload_success = ""

        if not files:
            return

        upload_file = files[0]
        self._pending_upload_data = upload_file.file.read()
        self._pending_upload_name = upload_file.filename or "unknown"
        self.upload_filename = self._pending_upload_name

    async def confirm_upload(self):
        """Upload the previously selected file with the description (called from button)."""
        self.upload_error = ""
        self.upload_success = ""

        if not self._pending_upload_data:
            self.upload_error = "Selecciona un archivo primero."
            return

        self.is_uploading = True

        from app.app import AppState
        app_state = await self.get_state(AppState)
        uid = app_state.user_id

        from app.upload import handle_upload

        # Run the blocking upload (file save + processing) in a thread pool
        # to avoid blocking the Granian event loop worker, which would cause
        # "Killing worker" errors during heavy operations like Whisper transcription.
        loop = asyncio.get_running_loop()
        success, message, file_info = await loop.run_in_executor(
            None,  # Uses default ThreadPoolExecutor
            lambda: handle_upload(
                user_id=uid,
                file_data=self._pending_upload_data,
                original_filename=self._pending_upload_name,
                description=self.upload_description,
            ),
        )

        if success:
            self.upload_success = message
            await self.load_user_files()
            self.show_upload_modal = False
        else:
            self.upload_error = message

        self.is_uploading = False
        self._pending_upload_data = b""
        self._pending_upload_name = ""

    async def refresh_files(self):
        """Refresh the file list (used for auto-refresh of processing status)."""
        from app.app import AppState
        app_state = await self.get_state(AppState)
        uid = app_state.user_id
        if not uid:
            return

        db = get_session()
        try:
            user_files = (
                db.query(File)
                .filter(File.user_id == uid)
                .order_by(File.uploaded_at.desc())
                .all()
            )
            self.files = [
                {
                    "id": f.id,
                    "original_filename": f.original_filename,
                    "file_type": f.file_type,
                    "file_size": f.file_size,
                    "file_size_display": format_file_size_py(f.file_size),
                    "description": f.description or "",
                    "uploaded_at": f.uploaded_at.isoformat() if f.uploaded_at else "",
                    "stored_filename": f.stored_filename,
                    "processing_status": f.processing_status or "pending",
                }
                for f in user_files
            ]
        except Exception as e:
            print(f"Error refreshing files: {e}")
        finally:
            db.close()

    def tick(self, _=None):
        """Periodic tick to auto-refresh file list when there are pending/processing files.
        
        Called from rx.call_script callback (recursive setTimeout).
        When there are active files, triggers a refresh and always schedules the next tick.
        The `_` parameter is optional and receives the result from the JavaScript callback.
        """
        self._refresh_tick += 1
        # Check if any files are still pending or processing
        has_active = any(
            f.get("processing_status") in ("pending", "processing")
            for f in self.files
        )
        events = []
        if has_active:
            # Schedule a refresh by calling the async method
            events.append(DashboardState.refresh_files)
        # Schedule the next tick via JavaScript setTimeout (5 seconds)
        # rx.call_script executes the JS, then calls the callback with the result
        events.append(
            rx.call_script(
                "setTimeout(() => null, 5000)",
                callback=DashboardState.tick,
            )
        )
        return events

    def view_file_detail(self, file_data: dict):
        """Set the selected file and navigate to detail page."""
        self.selected_file = file_data
        return rx.redirect(f"/file/{file_data['id']}")

    async def handle_logout(self):
        """Handle user logout."""
        from app.app import AppState
        app_state = await self.get_state(AppState)
        app_state.clear_user()
        self.files = []
        # Reset login/register form fields
        from app.pages.login import LoginState
        login_state = await self.get_state(LoginState)
        login_state.reset_form()
        return rx.redirect("/")

    async def delete_file(self, file_id: int):
        """Delete a file by its ID."""
        from app.app import AppState
        app_state = await self.get_state(AppState)
        uid = app_state.user_id
        if not uid:
            return

        from app.auth import delete_user_file
        success, message = delete_user_file(file_id, uid)
        if success:
            # Remove from local list
            self.files = [f for f in self.files if f.get("id") != file_id]
        else:
            print(f"Delete error: {message}")

    # ── Change Password ──────────────────────────────────────────

    def open_change_password_modal(self):
        """Open the change password modal."""
        self.show_change_password_modal = True
        self.cp_old_password = ""
        self.cp_new_password = ""
        self.cp_confirm_password = ""
        self.cp_error = ""
        self.cp_success = ""

    def close_change_password_modal(self):
        """Close the change password modal."""
        self.show_change_password_modal = False

    def set_cp_old_password(self, value: str):
        self.cp_old_password = value

    def set_cp_new_password(self, value: str):
        self.cp_new_password = value

    def set_cp_confirm_password(self, value: str):
        self.cp_confirm_password = value

    async def handle_change_password(self):
        """Handle change password form submission."""
        self.cp_error = ""
        self.cp_success = ""

        if self.cp_new_password != self.cp_confirm_password:
            self.cp_error = "Las contraseñas nuevas no coinciden."
            return

        from app.app import AppState
        app_state = await self.get_state(AppState)
        uid = app_state.user_id
        if not uid:
            return

        from app.auth import change_password
        success, message = change_password(uid, self.cp_old_password, self.cp_new_password)
        if success:
            self.cp_success = message
            self.cp_old_password = ""
            self.cp_new_password = ""
            self.cp_confirm_password = ""
        else:
            self.cp_error = message


def _modal_overlay(children):
    """Create a glassmorphism modal overlay."""
    return rx.box(
        rx.box(
            children,
            background_color="rgba(255, 255, 255, 0.95)",
            backdrop_filter="blur(20px)",
            border="1px solid rgba(255, 255, 255, 0.3)",
            border_radius="16px",
            padding="2rem",
            width="100%",
            max_width="500px",
            box_shadow="0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 40px rgba(0, 0, 0, 0.12)",
        ),
        # Overlay
        position="fixed",
        top="0",
        left="0",
        width="100vw",
        height="100vh",
        background_color="rgba(0, 0, 0, 0.3)",
        backdrop_filter="blur(4px)",
        display="flex",
        align_items="center",
        justify_content="center",
        z_index="200",
        padding="1rem",
    )


def _modal_header(title: str, on_close):
    """Create a modal header with title and close button."""
    return rx.hstack(
        rx.text(
            title,
            font_size="1.25rem",
            font_weight="700",
            color=TEXT_PRIMARY,
            letter_spacing="-0.3px",
        ),
        rx.spacer(),
        rx.button(
            rx.icon(tag="x", font_size="1.1rem"),
            on_click=on_close,
            variant="ghost",
            color=TEXT_SECONDARY,
            border_radius="8px",
            _hover={"color": TEXT_PRIMARY, "background_color": LIGHT_GRAY_BLUE},
        ),
        width="100%",
        align="center",
        margin_bottom="0.5rem",
    )


def _gradient_button(text, on_click, is_disabled=None, **props):
    """Create a gradient button for modals."""
    return rx.button(
        text,
        on_click=on_click,
        is_disabled=is_disabled,
        background=f"linear-gradient(135deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER})",
        color=TEXT_PRIMARY,
        font_weight="600",
        border="none",
        border_radius="10px",
        padding="0.8rem 1.5rem",
        width="100%",
        cursor="pointer",
        transition="all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
        box_shadow=f"0 4px 14px rgba(126, 200, 227, 0.35)",
        _hover={
            "transform": "translateY(-2px)",
            "box_shadow": f"0 6px 20px rgba(126, 200, 227, 0.5)",
        },
        _active={
            "transform": "translateY(0px)",
        },
        **props
    )


def upload_modal() -> rx.Component:
    """Upload file modal dialog."""
    return rx.cond(
        DashboardState.show_upload_modal,
        _modal_overlay(
            rx.vstack(
                _modal_header("Subir archivo", DashboardState.close_upload_modal),
                rx.text(
                    "Selecciona un archivo y añade una descripción opcional",
                    font_size="0.85rem",
                    color=TEXT_SECONDARY,
                    margin_bottom="0.5rem",
                ),
                # Upload area with Reflex upload component
                rx.upload(
                    rx.vstack(
                        rx.box(
                            rx.icon(
                                tag="cloud_upload",
                                color=PASTEL_BLUE,
                                font_size="2.5rem",
                            ),
                            padding="0.5rem",
                        ),
                        rx.cond(
                            DashboardState.upload_filename,
                            rx.text(
                                DashboardState.upload_filename,
                                font_size="0.95rem",
                                color=TEXT_PRIMARY,
                                font_weight="600",
                            ),
                            rx.text(
                                "Arrastra o haz clic para buscar",
                                font_size="0.95rem",
                                color=TEXT_PRIMARY,
                                font_weight="500",
                            ),
                        ),
                        rx.text(
                            "Se acepta cualquier tipo de archivo — extracción de texto para documentos, imágenes, audio y vídeo",
                            font_size="0.8rem",
                            color=TEXT_SECONDARY,
                            text_align="center",
                        ),
                        spacing="2",
                        align="center",
                        padding="2rem",
                    ),
                    border=f"2px dashed {PASTEL_BLUE}",
                    border_radius="12px",
                    background_color=LIGHT_GRAY_BLUE,
                    width="100%",
                    transition="all 0.2s ease",
                    _hover={
                        "background_color": "#E8F0FE",
                        "border_color": PASTEL_BLUE_HOVER,
                    },
                    id="file_upload",
                    on_drop=DashboardState.handle_file_selected,
                    multiple=False,
                    # Accept all files - no MIME filter
                    accept={},
                ),
                # Description
                rx.vstack(
                    rx.text(
                        "Descripción (opcional)",
                        font_size="0.85rem",
                        font_weight="600",
                        color=TEXT_PRIMARY,
                    ),
                    rx.text_area(
                        value=DashboardState.upload_description,
                        on_change=DashboardState.set_upload_description,
                        placeholder="Añade una descripción para este archivo...",
                        border=f"1px solid {BORDER_LIGHT}",
                        border_radius="10px",
                        padding="0.75rem",
                        font_size="0.95rem",
                        width="100%",
                        min_height="80px",
                        transition="all 0.2s ease",
                        _focus={
                            "border_color": PASTEL_BLUE,
                            "box_shadow": f"0 0 0 4px rgba(126, 200, 227, 0.2)",
                            "outline": "none",
                        },
                    ),
                    width="100%",
                    spacing="1",
                ),
                # Error message
                rx.cond(
                    DashboardState.upload_error,
                    rx.text(
                        DashboardState.upload_error,
                        color="#E53E3E",
                        font_size="0.85rem",
                        padding="0.75rem",
                        background_color="rgba(229, 62, 62, 0.08)",
                        border="1px solid rgba(229, 62, 62, 0.2)",
                        border_radius="8px",
                        width="100%",
                        text_align="center",
                    ),
                ),
                # Submit button
                _gradient_button(
                    rx.cond(
                        DashboardState.is_uploading,
                        rx.hstack(
                            rx.spinner(size="2", color=TEXT_PRIMARY),
                            rx.text("Subiendo..."),
                            spacing="2",
                        ),
                        rx.text("Subir archivo"),
                    ),
                    on_click=DashboardState.confirm_upload,
                    is_disabled=DashboardState.is_uploading,
                ),
                spacing="4",
                width="100%",
            ),
        ),
    )


def change_password_modal() -> rx.Component:
    """Change password modal dialog."""
    return rx.cond(
        DashboardState.show_change_password_modal,
        _modal_overlay(
            rx.vstack(
                _modal_header("Cambiar contraseña", DashboardState.close_change_password_modal),
                rx.text(
                    "Introduce tu contraseña actual y la nueva contraseña",
                    font_size="0.85rem",
                    color=TEXT_SECONDARY,
                    margin_bottom="0.5rem",
                ),
                # Old password
                rx.vstack(
                    rx.text("Contraseña actual", font_size="0.85rem", font_weight="600", color=TEXT_PRIMARY),
                    pastel_blue_input(
                        value=DashboardState.cp_old_password,
                        on_change=DashboardState.set_cp_old_password,
                        placeholder="Introduce tu contraseña actual",
                        type="password",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # New password
                rx.vstack(
                    rx.text("Nueva contraseña", font_size="0.85rem", font_weight="600", color=TEXT_PRIMARY),
                    pastel_blue_input(
                        value=DashboardState.cp_new_password,
                        on_change=DashboardState.set_cp_new_password,
                        placeholder="Introduce la nueva contraseña",
                        type="password",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Confirm new password
                rx.vstack(
                    rx.text("Confirmar nueva contraseña", font_size="0.85rem", font_weight="600", color=TEXT_PRIMARY),
                    pastel_blue_input(
                        value=DashboardState.cp_confirm_password,
                        on_change=DashboardState.set_cp_confirm_password,
                        placeholder="Confirma la nueva contraseña",
                        type="password",
                    ),
                    spacing="1",
                    width="100%",
                ),
                # Error message
                rx.cond(
                    DashboardState.cp_error,
                    rx.text(
                        DashboardState.cp_error,
                        color="#E53E3E",
                        font_size="0.85rem",
                        padding="0.75rem",
                        background_color="rgba(229, 62, 62, 0.08)",
                        border="1px solid rgba(229, 62, 62, 0.2)",
                        border_radius="8px",
                        width="100%",
                        text_align="center",
                    ),
                ),
                # Success message
                rx.cond(
                    DashboardState.cp_success,
                    rx.text(
                        DashboardState.cp_success,
                        color="#38A169",
                        font_size="0.85rem",
                        padding="0.75rem",
                        background_color="rgba(56, 161, 105, 0.08)",
                        border="1px solid rgba(56, 161, 105, 0.2)",
                        border_radius="8px",
                        width="100%",
                        text_align="center",
                    ),
                ),
                # Submit button
                _gradient_button(
                    "Cambiar contraseña",
                    on_click=DashboardState.handle_change_password,
                ),
                spacing="4",
                width="100%",
            ),
        ),
    )


def dashboard_page() -> rx.Component:
    """Main dashboard page with file grid."""
    return rx.box(
        # Navbar
        navbar(
            on_logout=DashboardState.handle_logout,
            on_change_password=DashboardState.open_change_password_modal,
        ),
        # Main content
        rx.vstack(
            # Header area with search and upload
            rx.hstack(
                section_title("Mis archivos"),
                rx.spacer(),
                rx.button(
                    rx.hstack(
                        rx.icon(tag="cloud_upload", font_size="1.1rem"),
                        rx.text("Subir", font_weight="600"),
                        spacing="2",
                    ),
                    on_click=DashboardState.open_upload_modal,
                    background=f"linear-gradient(135deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER})",
                    color=TEXT_PRIMARY,
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
                    _active={
                        "transform": "translateY(0px)",
                    },
                ),
                width="100%",
                align="center",
                spacing="3",
                margin_bottom="1.5rem",
            ),
            # File count subtitle
            rx.text(
                f"{DashboardState.files.length()} archivo(s) almacenados",
                font_size="0.85rem",
                color=TEXT_SECONDARY,
                margin_top="-1rem",
                margin_bottom="1rem",
                width="100%",
            ),
            # Search bar
            search_bar(
                value=DashboardState.search_query,
                on_change=DashboardState.set_search_query,
                on_submit=DashboardState.handle_search,
            ),
            # File grid
            rx.cond(
                DashboardState.is_searching,
                rx.box(
                    rx.spinner(size="3", color=PASTEL_BLUE),
                    padding="3rem",
                    text_align="center",
                ),
                rx.cond(
                    DashboardState.files.length() > 0,
                    rx.grid(
                        rx.foreach(
                            DashboardState.files,
                            lambda f: file_card(
                                file_data=f,
                                on_click=lambda: DashboardState.view_file_detail(f),
                                on_delete=lambda: DashboardState.delete_file(f.get("id")),
                            ),
                        ),
                        columns="4",
                        spacing="4",
                        width="100%",
                    ),
                    # Empty state
                    rx.box(
                        rx.vstack(
                            rx.box(
                                rx.icon(
                                    tag="folder-open",
                                    color=PASTEL_BLUE,
                                    font_size="4rem",
                                ),
                                padding="1rem",
                                background_color=LIGHT_GRAY_BLUE,
                                border_radius="16px",
                            ),
                            rx.text(
                                "Aún no hay archivos",
                                font_size="1.25rem",
                                font_weight="600",
                                color=TEXT_PRIMARY,
                            ),
                            rx.text(
                                "¡Sube tu primer archivo para empezar!",
                                font_size="0.9rem",
                                color=TEXT_SECONDARY,
                            ),
                            rx.button(
                                "Subir archivo",
                                on_click=DashboardState.open_upload_modal,
                                background=f"linear-gradient(135deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER})",
                                color=TEXT_PRIMARY,
                                font_weight="600",
                                border="none",
                                border_radius="10px",
                                padding="0.75rem 1.5rem",
                                cursor="pointer",
                                box_shadow=f"0 4px 14px rgba(126, 200, 227, 0.35)",
                                _hover={
                                    "transform": "translateY(-2px)",
                                    "box_shadow": f"0 6px 20px rgba(126, 200, 227, 0.5)",
                                },
                            ),
                            spacing="4",
                            align="center",
                            padding="4rem 2rem",
                        ),
                        width="100%",
                    ),
                ),
            ),
            width="100%",
            max_width="1200px",
            padding="2rem",
            align="start",
        ),
        # Upload modal overlay
        upload_modal(),
        # Change password modal overlay
        change_password_modal(),
        background_color=LIGHT_GRAY_BLUE,
        min_height="100vh",
        width="100%",
    )
