"""File card component for ReQperacion dashboard."""

import os
import reflex as rx
from app.styles.theme import (
    PASTEL_BLUE, PASTEL_BLUE_HOVER, DEEP_SOFT_BLUE, TEXT_PRIMARY, TEXT_SECONDARY, WHITE, BORDER_LIGHT,
    SOFT_BLUE, LIGHT_GRAY_BLUE,
)


def get_file_icon(file_type):
    """Get an icon name based on file type category using rx.match."""
    return rx.match(
        file_type,
        ("image", "image"),
        ("document", "file-text"),
        ("spreadsheet", "table"),
        ("text", "file"),
        ("code", "terminal"),
        ("audio", "music"),
        ("video", "video"),
        "file",  # default
    )


def get_file_color(file_type):
    """Get a color for the file type badge using rx.match."""
    return rx.match(
        file_type,
        ("image", "#9AE6B4"),
        ("document", "#B8D4E8"),
        ("spreadsheet", "#FBD38D"),
        ("text", "#A8D5E2"),
        ("code", "#E9D8FD"),
        ("audio", "#FBB6CE"),
        ("video", "#E9D8FD"),
        "#E2E8F0",  # default
    )


def format_file_size(size_bytes):
    """Format file size in human-readable format (for plain ints)."""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.1f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"


def _get_status_color(status):
    """Get a color for the processing status badge using rx.match."""
    return rx.match(
        status,
        ("pending", "#FBD38D"),       # yellow
        ("processing", "#90CDF4"),    # blue
        ("completed", "#90CDF4"),     # blue
        ("failed", "#FEB2B2"),        # red
        "#E2E8F0",                    # default gray
    )


def _get_status_label(status):
    """Get a human-readable label for the processing status using rx.match."""
    return rx.match(
        status,
        ("pending", "Pendiente"),
        ("processing", "Procesando..."),
        ("completed", "Procesado"),
        ("failed", "Error"),
        status,  # fallback: show the raw status value
    )


def file_card(file_data: dict, on_click, on_delete=None):
    """Create a file card for the dashboard grid."""
    file_type = file_data.get("file_type", "other")
    icon_name = get_file_icon(file_type)
    badge_color = get_file_color(file_type)
    description = file_data.get("description", "")
    uploaded_at = file_data.get("uploaded_at", "")
    processing_status = file_data.get("processing_status", "pending")
    status_color = _get_status_color(processing_status)
    status_label = _get_status_label(processing_status)
    file_id = file_data.get("id", 0)
    username = file_data.get("username", "")

    return rx.box(
        # Blue left accent bar (visible on hover)
        rx.box(
            position="absolute",
            left="0",
            top="0",
            width="4px",
            height="100%",
            background=f"linear-gradient(180deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER})",
            border_radius="0 4px 4px 0",
            opacity="0",
            transition="opacity 0.25s ease",
            _hover={
                "opacity": "1",
            },
        ),
        rx.vstack(
            # Top section: icon + info
            rx.hstack(
                # File icon area (top-left, compact)
                rx.box(
                    rx.icon(
                        tag=icon_name,
                        color=PASTEL_BLUE,
                        font_size="1.4rem",
                    ),
                    background_color=LIGHT_GRAY_BLUE,
                    border_radius="10px",
                    padding="0.6rem",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                    min_width="2.8rem",
                    min_height="2.8rem",
                ),
                # File info
                rx.vstack(
                    rx.text(
                        file_data.get("original_filename", "Unknown"),
                        font_size="0.9rem",
                        font_weight="600",
                        color=TEXT_PRIMARY,
                        truncate=True,
                        width="100%",
                    ),
                    rx.text(
                        rx.cond(description != "", description, "Sin descripción"),
                        font_size="0.75rem",
                        color=TEXT_SECONDARY,
                        truncate=True,
                        width="100%",
                        no_of_lines=1,
                    ),
                    # Username (only shown when present, e.g. in explore tab)
                    rx.cond(
                        username != "",
                        rx.text(
                            f"Subido por {username}",
                            font_size="0.7rem",
                            color=DEEP_SOFT_BLUE,
                            font_weight="500",
                            width="100%",
                        ),
                    ),
                    spacing="1",
                    width="100%",
                ),
                spacing="3",
                width="100%",
                align="center",
            ),
            # Bottom section: badges + delete button
            rx.hstack(
                rx.box(
                    file_type,
                    font_size="0.65rem",
                    font_weight="600",
                    color=TEXT_PRIMARY,
                    background_color=badge_color,
                    padding="0.1rem 0.4rem",
                    border_radius="4px",
                ),
                rx.text(
                    file_data.get("file_size_display", ""),
                    font_size="0.7rem",
                    color=TEXT_SECONDARY,
                ),
                # Processing status badge
                rx.box(
                    rx.cond(
                        processing_status == "processing",
                        rx.hstack(
                            rx.spinner(size="1", color=TEXT_PRIMARY),
                            rx.text(status_label, font_size="0.65rem", font_weight="600"),
                            spacing="1",
                            align="center",
                        ),
                        rx.text(status_label, font_size="0.65rem", font_weight="600"),
                    ),
                    background_color=status_color,
                    padding="0.1rem 0.4rem",
                    border_radius="4px",
                ),
                rx.spacer(),
                # Delete button (bottom-right) - only shown when on_delete is provided
                rx.cond(
                    on_delete is not None,
                    rx.button(
                        rx.icon(tag="trash_2", font_size="0.85rem", color=WHITE),
                        on_click=on_delete,
                        background_color="#E53E3E",
                        border_radius="6px",
                        padding="0.25rem",
                        width="1.6rem",
                        height="1.6rem",
                        display="flex",
                        align_items="center",
                        justify_content="center",
                        cursor="pointer",
                        opacity="0.6",
                        transition="all 0.2s ease",
                        _hover={
                            "background_color": "#C53030",
                            "transform": "scale(1.1)",
                            "opacity": "1",
                            "box_shadow": "0 2px 8px rgba(229, 62, 62, 0.4)",
                        },
                    ),
                ),
                spacing="2",
                align="center",
                width="100%",
                flex_wrap="wrap",
            ),
            spacing="3",
            width="100%",
            align="start",
        ),
        on_click=on_click,
        background_color=WHITE,
        border=f"1px solid {BORDER_LIGHT}",
        border_radius="14px",
        padding="1rem",
        cursor="pointer",
        position="relative",
        overflow="hidden",
        transition="all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
        box_shadow="0 1px 3px rgba(0, 0, 0, 0.04)",
        _hover={
            "box_shadow": "0 4px 20px rgba(126, 200, 227, 0.25), 0 1px 3px rgba(0, 0, 0, 0.04)",
            "border_color": PASTEL_BLUE,
            "transform": "translateY(-3px)",
        },
        width="100%",
    )
