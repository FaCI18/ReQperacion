"""Página combinada de Inicio de Sesión / Registro para ReQperacion.

Lado izquierdo: formulario de inicio de sesión
Lado derecho: formulario de registro
Separados por un divisor vertical.
"""

import reflex as rx
from app.styles.theme import (
    PASTEL_BLUE, PASTEL_BLUE_HOVER, DEEP_SOFT_BLUE, TEXT_PRIMARY, TEXT_SECONDARY,
    WHITE, BORDER_LIGHT, LIGHT_GRAY_BLUE, ERROR, pastel_blue_input,
)


class LoginState(rx.State):
    """State for the login/register page."""
    # Login fields
    login_username: str = ""
    login_password: str = ""
    # Register fields
    register_username: str = ""
    register_email: str = ""
    register_password: str = ""
    register_confirm: str = ""
    # UI state
    error_message: str = ""
    success_message: str = ""

    # Explicit setters (auto_setters deprecated in 0.8.9)
    def set_login_username(self, value: str):
        self.login_username = value

    def set_login_password(self, value: str):
        self.login_password = value

    def set_register_username(self, value: str):
        self.register_username = value

    def set_register_email(self, value: str):
        self.register_email = value

    def set_register_password(self, value: str):
        self.register_password = value

    def set_register_confirm(self, value: str):
        self.register_confirm = value

    def clear_messages(self):
        self.error_message = ""
        self.success_message = ""

    def reset_form(self):
        """Reset all form fields and messages."""
        self.login_username = ""
        self.login_password = ""
        self.register_username = ""
        self.register_email = ""
        self.register_password = ""
        self.register_confirm = ""
        self.error_message = ""
        self.success_message = ""

    async def handle_login(self):
        """Handle login form submission."""
        self.clear_messages()
        from app.auth import login_user

        success, message, user = login_user(
            self.login_username,
            self.login_password,
        )

        if success and user:
            # Set user in AppState (get_state is async in Reflex 0.8.17)
            from app.app import AppState
            app_state = await self.get_state(AppState)
            app_state.set_user(user.id, user.username)
            self.success_message = message
            return rx.redirect("/dashboard")
        else:
            self.error_message = message

    def handle_register(self):
        """Handle register form submission."""
        self.clear_messages()

        if self.register_password != self.register_confirm:
            self.error_message = "Las contraseñas no coinciden."
            return

        from app.auth import register_user

        success, message = register_user(
            self.register_username,
            self.register_email,
            self.register_password,
        )

        if success:
            self.success_message = message
            # Auto-fill login fields
            self.login_username = self.register_username
            self.login_password = self.register_password
            # Clear register fields
            self.register_username = ""
            self.register_email = ""
            self.register_password = ""
            self.register_confirm = ""
        else:
            self.error_message = message


def _form_button(text: str, on_click, **props):
    """Create a styled form button with gradient."""
    return rx.button(
        text,
        on_click=on_click,
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


def login_form() -> rx.Component:
    """Left side: Login form."""
    return rx.vstack(
        rx.text(
            "Bienvenido de nuevo",
            font_size="1.5rem",
            font_weight="700",
            color=TEXT_PRIMARY,
            letter_spacing="-0.3px",
        ),
        rx.text(
            "Inicia sesión en tu cuenta",
            font_size="0.9rem",
            color=TEXT_SECONDARY,
            margin_bottom="1.5rem",
        ),
        # Username
        rx.vstack(
            rx.text("Usuario o correo", font_size="0.85rem", font_weight="600", color=TEXT_PRIMARY),
            pastel_blue_input(
                value=LoginState.login_username,
                on_change=LoginState.set_login_username,
                placeholder="Introduce tu usuario o correo",
            ),
            spacing="1",
            width="100%",
        ),
        # Password
        rx.vstack(
            rx.text("Contraseña", font_size="0.85rem", font_weight="600", color=TEXT_PRIMARY),
            pastel_blue_input(
                value=LoginState.login_password,
                on_change=LoginState.set_login_password,
                placeholder="Introduce tu contraseña",
                type="password",
            ),
            spacing="1",
            width="100%",
        ),
        # Error message
        rx.cond(
            LoginState.error_message,
            rx.text(
                LoginState.error_message,
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
        _form_button("Iniciar sesión", LoginState.handle_login),
        spacing="4",
        width="100%",
        flex="1",
        padding="2rem",
    )


def register_form() -> rx.Component:
    """Right side: Register form."""
    return rx.vstack(
        rx.text(
            "Crear cuenta",
            font_size="1.5rem",
            font_weight="700",
            color=TEXT_PRIMARY,
            letter_spacing="-0.3px",
        ),
        rx.text(
            "Únete a ReQperacion hoy",
            font_size="0.9rem",
            color=TEXT_SECONDARY,
            margin_bottom="1.5rem",
        ),
        # Username
        rx.vstack(
            rx.text("Usuario", font_size="0.85rem", font_weight="600", color=TEXT_PRIMARY),
            pastel_blue_input(
                value=LoginState.register_username,
                on_change=LoginState.set_register_username,
                placeholder="Elige un nombre de usuario",
            ),
            spacing="1",
            width="100%",
        ),
        # Email
        rx.vstack(
            rx.text("Correo electrónico", font_size="0.85rem", font_weight="600", color=TEXT_PRIMARY),
            pastel_blue_input(
                value=LoginState.register_email,
                on_change=LoginState.set_register_email,
                placeholder="Introduce tu correo electrónico",
                type="email",
            ),
            spacing="1",
            width="100%",
        ),
        # Password
        rx.vstack(
            rx.text("Contraseña", font_size="0.85rem", font_weight="600", color=TEXT_PRIMARY),
            pastel_blue_input(
                value=LoginState.register_password,
                on_change=LoginState.set_register_password,
                placeholder="Crea una contraseña",
                type="password",
            ),
            spacing="1",
            width="100%",
        ),
        # Confirm password
        rx.vstack(
            rx.text("Confirmar contraseña", font_size="0.85rem", font_weight="600", color=TEXT_PRIMARY),
            pastel_blue_input(
                value=LoginState.register_confirm,
                on_change=LoginState.set_register_confirm,
                placeholder="Confirma tu contraseña",
                type="password",
            ),
            spacing="1",
            width="100%",
        ),
        # Success message
        rx.cond(
            LoginState.success_message,
            rx.text(
                LoginState.success_message,
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
        _form_button("Registrarse", LoginState.handle_register),
        spacing="4",
        width="100%",
        flex="1",
        padding="2rem",
    )


def login_page() -> rx.Component:
    """Combined login/register page."""
    return rx.box(
        # Decorative background shapes
        rx.box(
            position="absolute",
            top="-100px",
            right="-100px",
            width="350px",
            height="350px",
            border_radius="50%",
            background=f"radial-gradient(circle, rgba(126, 200, 227, 0.3) 0%, transparent 70%)",
            pointer_events="none",
        ),
        rx.box(
            position="absolute",
            bottom="-120px",
            left="-120px",
            width="300px",
            height="300px",
            border_radius="50%",
            background=f"radial-gradient(circle, rgba(90, 189, 217, 0.25) 0%, transparent 70%)",
            pointer_events="none",
        ),
        rx.box(
            position="absolute",
            top="35%",
            left="5%",
            width="200px",
            height="200px",
            border_radius="50%",
            background=f"radial-gradient(circle, rgba(126, 200, 227, 0.2) 0%, transparent 70%)",
            pointer_events="none",
        ),
        rx.vstack(
            # Logo
            rx.hstack(
                rx.box(
                    rx.icon(tag="cloud", color=WHITE, font_size="1.8rem"),
                    background=f"linear-gradient(135deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER})",
                    border_radius="14px",
                    padding="0.6rem",
                    box_shadow=f"0 4px 14px rgba(126, 200, 227, 0.4)",
                ),
                rx.text(
                    "ReQperacion",
                    font_size="2rem",
                    font_weight="700",
                    color=TEXT_PRIMARY,
                    letter_spacing="-1px",
                ),
                spacing="3",
                align="center",
                margin_bottom="1.5rem",
            ),
            # Main card with login + register
            rx.box(
                # Blue top accent strip with gradient
                rx.box(
                    height="5px",
                    width="100%",
                    background=f"linear-gradient(90deg, {PASTEL_BLUE}, {PASTEL_BLUE_HOVER}, {DEEP_SOFT_BLUE})",
                    border_radius="16px 16px 0 0",
                ),
                rx.hstack(
                    # Login form (left)
                    login_form(),
                    # Vertical divider
                    rx.box(
                        width="1px",
                        height="auto",
                        background=f"linear-gradient(180deg, transparent, {BORDER_LIGHT}, transparent)",
                        min_height="400px",
                        align_self="stretch",
                    ),
                    # Register form (right)
                    register_form(),
                    spacing="0",
                    align="stretch",
                    width="100%",
                ),
                background_color="rgba(255, 255, 255, 0.92)",
                backdrop_filter="blur(16px)",
                border="1px solid rgba(255, 255, 255, 0.3)",
                border_radius="16px",
                box_shadow="0 1px 3px rgba(0, 0, 0, 0.04), 0 8px 32px rgba(0, 0, 0, 0.08)",
                width="100%",
                max_width="900px",
                overflow="hidden",
            ),
            align="center",
            justify="center",
            min_height="100vh",
            width="100%",
            padding="2rem",
        ),
        background_color=LIGHT_GRAY_BLUE,
        width="100%",
        min_height="100vh",
        position="relative",
        overflow="hidden",
    )
