"""Navigation bar component for ReQperacion."""

import reflex as rx
from app.styles.theme import PASTEL_BLUE, PASTEL_BLUE_HOVER, DEEP_SOFT_BLUE, TEXT_PRIMARY, TEXT_SECONDARY, WHITE, LIGHT_GRAY_BLUE


def navbar(on_logout, on_change_password=None):
    """Create the top navigation bar with a user dropdown menu."""
    from app.app import AppState

    return rx.box(
        rx.hstack(
            # Logo / App name
            rx.hstack(
                rx.box(
                    rx.icon(
                        tag="cloud",
                        color=WHITE,
                        font_size="1.3rem",
                    ),
                    background=f"linear-gradient(135deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER})",
                    border_radius="10px",
                    padding="0.5rem",
                    display="flex",
                    align_items="center",
                    justify_content="center",
                ),
                rx.text(
                    "ReQperacion",
                    font_size="1.4rem",
                    font_weight="700",
                    color=TEXT_PRIMARY,
                    letter_spacing="-0.5px",
                ),
                spacing="3",
                align="center",
            ),
            # Spacer
            rx.spacer(),
            # User dropdown menu
            rx.menu.root(
                rx.menu.trigger(
                    rx.button(
                        rx.hstack(
                            rx.box(
                                rx.icon(
                                    tag="user",
                                    color=WHITE,
                                    font_size="0.9rem",
                                ),
                                background=f"linear-gradient(135deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER})",
                                border_radius="8px",
                                padding="0.35rem",
                                display="flex",
                                align_items="center",
                                justify_content="center",
                            ),
                            rx.text(
                                AppState.username,
                                font_size="0.9rem",
                                color=TEXT_PRIMARY,
                                font_weight="600",
                            ),
                            rx.icon(
                                tag="chevron-down",
                                color=TEXT_SECONDARY,
                                font_size="0.85rem",
                            ),
                            spacing="2",
                            align="center",
                        ),
                        variant="ghost",
                        padding="0.4rem 0.75rem",
                        border_radius="10px",
                        _hover={
                            "background_color": "rgba(126, 200, 227, 0.1)",
                        },
                    ),
                ),
                rx.menu.content(
                    rx.menu.item(
                        rx.hstack(
                            rx.icon(tag="lock", font_size="0.9rem", color=TEXT_SECONDARY),
                            rx.text("Cambiar contraseña", font_size="0.85rem", color=TEXT_PRIMARY),
                            spacing="2",
                        ),
                        on_click=on_change_password,
                    ),
                    rx.menu.separator(),
                    rx.menu.item(
                        rx.hstack(
                            rx.icon(tag="log-out", font_size="0.9rem", color="#E53E3E"),
                            rx.text("Cerrar sesión", font_size="0.85rem", color="#E53E3E"),
                            spacing="2",
                        ),
                        on_click=on_logout,
                    ),
                ),
            ),
            align="center",
            width="100%",
            padding="0.75rem 2rem",
        ),
        background_color="rgba(255, 255, 255, 0.92)",
        backdrop_filter="blur(16px)",
        border_bottom="1px solid rgba(226, 232, 240, 0.8)",
        box_shadow="0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 16px rgba(0, 0, 0, 0.04)",
        position="sticky",
        top="0",
        z_index="100",
        width="100%",
    )
