"""Authentication module for ReQperacion."""

import bcrypt
from sqlalchemy import text
from app.models import User, get_session


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(
        password.encode("utf-8"),
        password_hash.encode("utf-8")
    )


def register_user(username: str, email: str, password: str) -> tuple[bool, str]:
    """
    Register a new user.
    Returns (success: bool, message: str).
    """
    if not username or not email or not password:
        return False, "Todos los campos son obligatorios."

    if len(username) < 3:
        return False, "El usuario debe tener al menos 3 caracteres."

    if len(password) < 6:
        return False, "La contraseña debe tener al menos 6 caracteres."

    db = get_session()
    try:
        # Check if username or email already exists
        existing = db.query(User).filter(
            (User.username == username) | (User.email == email)
        ).first()

        if existing:
            if existing.username == username:
                return False, "El nombre de usuario ya está en uso."
            return False, "El correo electrónico ya está registrado."

        # Create new user
        password_hash = hash_password(password)
        new_user = User(
            username=username,
            email=email,
            password_hash=password_hash,
        )
        db.add(new_user)
        db.commit()
        return True, "¡Registro exitoso!"

    except Exception as e:
        db.rollback()
        return False, f"Error al registrarse: {str(e)}"
    finally:
        db.close()


def login_user(username: str, password: str) -> tuple[bool, str, User | None]:
    """
    Authenticate a user.
    Returns (success: bool, message: str, user: User | None).
    """
    if not username or not password:
        return False, "Usuario y contraseña son obligatorios.", None

    db = get_session()
    try:
        user = db.query(User).filter(
            (User.username == username) | (User.email == username)
        ).first()

        if not user:
            return False, "Usuario o contraseña incorrectos.", None

        if not verify_password(password, user.password_hash):
            return False, "Usuario o contraseña incorrectos.", None

        return True, "¡Inicio de sesión exitoso!", user

    except Exception as e:
        return False, f"Error al iniciar sesión: {str(e)}", None
    finally:
        db.close()


def change_password(user_id: int, old_password: str, new_password: str) -> tuple[bool, str]:
    """
    Change a user's password.
    Returns (success: bool, message: str).
    """
    if not old_password or not new_password:
        return False, "Ambos campos son obligatorios."

    if len(new_password) < 6:
        return False, "La nueva contraseña debe tener al menos 6 caracteres."

    db = get_session()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return False, "Usuario no encontrado."

        if not verify_password(old_password, user.password_hash):
            return False, "La contraseña actual no es correcta."

        user.password_hash = hash_password(new_password)
        db.commit()
        return True, "Contraseña cambiada correctamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al cambiar la contraseña: {str(e)}"
    finally:
        db.close()


def delete_user_file(file_id: int, user_id: int) -> tuple[bool, str]:
    """
    Delete a file record and its associated data.
    Returns (success: bool, message: str).
    """
    import os
    from app.models import File, ExtractedText, FileTag
    db = get_session()
    try:
        file_record = db.query(File).filter(
            File.id == file_id,
            File.user_id == user_id,
        ).first()
        if not file_record:
            return False, "Archivo no encontrado."

        # Delete extracted text
        db.query(ExtractedText).filter(ExtractedText.file_id == file_id).delete()
        # Delete tags
        db.query(FileTag).filter(FileTag.file_id == file_id).delete()
        # Delete the file from disk
        file_path = file_record.file_path
        db.delete(file_record)
        db.commit()

        # Remove file from disk after DB commit
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except OSError:
                pass  # Non-critical if file is already gone

        return True, "Archivo eliminado correctamente."
    except Exception as e:
        db.rollback()
        return False, f"Error al eliminar el archivo: {str(e)}"
    finally:
        db.close()
