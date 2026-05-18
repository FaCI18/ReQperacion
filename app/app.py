"""ReQperacion - Main Reflex Application.

A Google Drive-like platform for file upload, document processing,
OCR text extraction, and full-text search.
"""

import os
import reflex as rx
from starlette.responses import FileResponse, JSONResponse
from app.styles.theme import get_theme, global_styles
from app.pages.login import login_page
from app.pages.dashboard import dashboard_page, DashboardState
from app.pages.file_detail import file_detail_page, FileDetailState
from app.models import init_db


class AppState(rx.State):
    """Global application state."""
    user_id: int = 0
    username: str = ""

    def set_user(self, user_id: int, username: str):
        """Set the authenticated user."""
        self.user_id = user_id
        self.username = username

    def clear_user(self):
        """Clear the authenticated user."""
        self.user_id = 0
        self.username = ""


def index() -> rx.Component:
    """Root route - login/register page."""
    return login_page()


# Define the app
app = rx.App(
    theme=get_theme(),
    style=global_styles(),
)


async def serve_file(request):
    """
    Serve uploaded files for preview and download.
    
    The URL path is like /api/files/1/uuid-filename.jpg
    which maps to /data/uploads/1/uuid-filename.jpg
    
    For downloads, pass ?download=1&filename=original_name.ext
    """
    upload_folder = os.environ.get("UPLOAD_FOLDER", "/data/uploads")
    
    # Extract the relative path from the request URL
    # URL: /api/files/1/uuid-filename.jpg
    # We want: 1/uuid-filename.jpg
    path = request.url.path
    prefix = "/api/files/"
    if path.startswith(prefix):
        relative_path = path[len(prefix):]
    else:
        return JSONResponse(
            content={"error": "Ruta inválida"},
            status_code=400,
        )
    
    full_path = os.path.join(upload_folder, relative_path)
    
    # Security: prevent path traversal
    real_upload = os.path.realpath(upload_folder)
    real_full = os.path.realpath(full_path)
    if not real_full.startswith(real_upload):
        return JSONResponse(
            content={"error": "Acceso denegado"},
            status_code=403,
        )
    
    if not os.path.exists(full_path) or not os.path.isfile(full_path):
        return JSONResponse(
            content={"error": "Archivo no encontrado"},
            status_code=404,
        )
    
    # Check if this is a download request
    download = request.query_params.get("download", "0")
    filename = request.query_params.get("filename", None)
    
    headers = {}
    if download == "1":
        # Force download with Content-Disposition: attachment
        if filename:
            # Sanitize filename for header (RFC 5987)
            import urllib.parse
            encoded_filename = urllib.parse.quote(filename)
            headers["Content-Disposition"] = f'attachment; filename="{filename}"; filename*=UTF-8\'\'{encoded_filename}'
        else:
            headers["Content-Disposition"] = "attachment"
    
    return FileResponse(full_path, headers=headers)


# Add the file-serving route to the FastAPI/Starlette app
app._api.add_route(
    "/api/files/{path:path}",
    serve_file,
    methods=["GET"],
)


# Add pages
app.add_page(
    index,
    route="/",
    title="ReQperacion - Iniciar sesión",
)

app.add_page(
    dashboard_page,
    route="/dashboard",
    title="ReQperacion - Mis archivos",
    on_load=[
        DashboardState.load_user_files,
        DashboardState.load_explore_files,
        DashboardState.load_users,
    ],
)

app.add_page(
    file_detail_page,
    route="/file/[file_id]",
    title="ReQperacion - Detalle del archivo",
    on_load=FileDetailState.load_file,
)


if __name__ == "__main__":
    # Initialize database tables
    init_db()
    app.run()
