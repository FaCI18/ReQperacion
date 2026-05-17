"""Pastel blue theme configuration for ReQperacion."""

import reflex as rx

# ── Color Palette ──────────────────────────────────────────────
# Vibrant pastel blue accents on white background

WHITE = "#FFFFFF"
LIGHT_GRAY_BLUE = "#F0F4F8"
# More vibrant pastel blue - still soft but with more presence
PASTEL_BLUE = "#7EC8E3"
PASTEL_BLUE_HOVER = "#5DBAD9"
# Deeper blue for accents (borders, secondary elements)
DEEP_SOFT_BLUE = "#5A9DBF"
# Very light blue for backgrounds
LIGHT_BLUE_BG = "#E3F0F7"
SOFT_BLUE = "#B8D4E8"
TEXT_PRIMARY = "#2D3748"
TEXT_SECONDARY = "#718096"
SUCCESS = "#9AE6B4"
ERROR = "#FEB2B2"
BORDER_LIGHT = "#E2E8F0"

# ── Common Styles ──────────────────────────────────────────────

def pastel_blue_button(text, on_click=None, **props):
    """Create a pastel blue button with consistent styling."""
    return rx.button(
        text,
        on_click=on_click,
        background=f"linear-gradient(135deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER})",
        color=TEXT_PRIMARY,
        font_weight="600",
        border="none",
        border_radius="10px",
        padding="0.75rem 1.5rem",
        cursor="pointer",
        transition="all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
        box_shadow=f"0 4px 14px rgba(126, 200, 227, 0.35)",
        _hover={
            "transform": "translateY(-2px)",
            "box_shadow": f"0 6px 20px rgba(126, 200, 227, 0.5)",
        },
        _active={
            "transform": "translateY(0px)",
            "box_shadow": f"0 2px 8px rgba(126, 200, 227, 0.3)",
        },
        **props
    )


def pastel_blue_input(**props):
    """Create a styled input field with pastel blue focus."""
    return rx.input(
        border=f"2px solid {BORDER_LIGHT}",
        border_radius="10px",
        padding="1rem 1.25rem",
        font_size="1rem",
        width="100%",
        min_height="56px",
        background_color=WHITE,
        color=TEXT_PRIMARY,
        transition="all 0.2s ease",
        _focus={
            "border_color": PASTEL_BLUE,
            "box_shadow": f"0 0 0 4px rgba(126, 200, 227, 0.2)",
            "outline": "none",
        },
        _placeholder={
            "color": "#2D3748",
            "opacity": "0.75",
        },
        **props
    )


def card(children, **props):
    """Create a card container with pastel blue styling."""
    return rx.box(
        children,
        background_color=WHITE,
        border=f"1px solid {BORDER_LIGHT}",
        border_radius="16px",
        box_shadow="0 1px 3px rgba(0, 0, 0, 0.04), 0 4px 16px rgba(0, 0, 0, 0.04)",
        padding="1.5rem",
        transition="all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
        _hover={
            "box_shadow": "0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 24px rgba(0, 0, 0, 0.08)",
            "transform": "translateY(-1px)",
        },
        **props
    )


def glass_card(children, **props):
    """Create a glassmorphism-style card."""
    return rx.box(
        children,
        background_color="rgba(255, 255, 255, 0.85)",
        backdrop_filter="blur(12px)",
        border=f"1px solid rgba(255, 255, 255, 0.3)",
        border_radius="16px",
        box_shadow="0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.06)",
        padding="1.5rem",
        transition="all 0.25s cubic-bezier(0.4, 0, 0.2, 1)",
        _hover={
            "box_shadow": "0 1px 3px rgba(0, 0, 0, 0.04), 0 12px 40px rgba(0, 0, 0, 0.1)",
        },
        **props
    )


def section_title(text: str, **props):
    """Create a styled section title with a blue left accent."""
    return rx.hstack(
        rx.box(
            width="4px",
            height="28px",
            background=f"linear-gradient(180deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER})",
            border_radius="0 4px 4px 0",
        ),
        rx.text(
            text,
            font_size="1.5rem",
            font_weight="700",
            color=TEXT_PRIMARY,
            letter_spacing="-0.3px",
        ),
        spacing="3",
        align="center",
        **props
    )


# ── Reflex Theme ───────────────────────────────────────────────

def get_theme():
    """Return the Reflex theme configuration."""
    return rx.theme(
        appearance="light",
        has_background=True,
        radius="medium",
        accent_color="blue",
        gray_color="slate",
    )


# ── Global Styles ──────────────────────────────────────────────

def global_styles():
    """Return global style overrides."""
    return {
        "body": {
            "background_color": LIGHT_GRAY_BLUE,
            "color": TEXT_PRIMARY,
            "font_family": "Inter, -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
            "background_image": "radial-gradient(ellipse at 20% 50%, rgba(126, 200, 227, 0.06) 0%, transparent 50%), radial-gradient(ellipse at 80% 20%, rgba(90, 189, 217, 0.04) 0%, transparent 50%)",
            "background_attachment": "fixed",
        },
        "::selection": {
            "background_color": PASTEL_BLUE,
            "color": WHITE,
        },
    }
