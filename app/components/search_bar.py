"""Search bar component for ReQperacion."""

import reflex as rx
from app.styles.theme import (
    PASTEL_BLUE, TEXT_PRIMARY, TEXT_SECONDARY, WHITE, BORDER_LIGHT,
)


def search_bar(value, on_change, on_submit, placeholder="Buscar archivos..."):
    """Create a search bar with pastel blue styling."""
    return rx.box(
        rx.hstack(
            rx.icon(
                tag="search",
                color=TEXT_SECONDARY,
                font_size="1.1rem",
            ),
            rx.input(
                value=value,
                on_change=on_change,
                on_key_down=on_submit,
                placeholder=placeholder,
                variant="soft",
                border="none",
                background_color="transparent",
                font_size="0.95rem",
                color=TEXT_PRIMARY,
                width="100%",
                _placeholder={
                    "color": "#2D3748",
                    "opacity": "0.75",
                },
                _focus={
                    "outline": "none",
                    "border": "none",
                },
            ),
            rx.cond(
                value != "",
                rx.button(
                    rx.icon(tag="x", font_size="0.85rem"),
                    on_click=lambda: on_change(""),
                    variant="ghost",
                    color=TEXT_SECONDARY,
                    padding="0.2rem",
                    _hover={"color": TEXT_PRIMARY},
                ),
            ),
            spacing="2",
            align="center",
            width="100%",
            padding="0.6rem 1.25rem",
        ),
        background_color=WHITE,
        border=f"2px solid {BORDER_LIGHT}",
        border_radius="12px",
        transition="all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
        box_shadow="0 1px 3px rgba(0, 0, 0, 0.04)",
        _hover={
            "border_color": PASTEL_BLUE,
            "box_shadow": "0 2px 12px rgba(126, 200, 227, 0.2)",
        },
        _focus_within={
            "border_color": PASTEL_BLUE,
            "box_shadow": "0 2px 16px rgba(126, 200, 227, 0.25)",
        },
        width="100%",
        max_width="600px",
    )
