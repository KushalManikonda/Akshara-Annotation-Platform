from typing import Optional

from sqlalchemy.orm import Session

from database.database import SessionLocal
from database.enums import UserRole
from database.models import User
from utils.security import hash_password


def get_db() -> Session:
    """Create a new database session."""
    return SessionLocal()


def get_all_users() -> list[User]:
    """Return all users ordered by creation date."""

    db = get_db()

    try:
        return (
            db.query(User)
            .order_by(User.created_at.desc())
            .all()
        )

    finally:
        db.close()


def get_user_by_id(user_id: str) -> Optional[User]:
    """Return a user by ID."""

    db = get_db()

    try:
        return (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

    finally:
        db.close()


def get_user_by_username(username: str) -> Optional[User]:
    """Return a user by username."""

    db = get_db()

    try:
        return (
            db.query(User)
            .filter(User.username == username)
            .first()
        )

    finally:
        db.close()


def get_user_by_email(email: str) -> Optional[User]:
    """Return a user by email."""

    db = get_db()

    try:
        return (
            db.query(User)
            .filter(User.email == email)
            .first()
        )

    finally:
        db.close()


def create_user(
    username: str,
    email: str,
    password: str,
    role: UserRole,
) -> Optional[User]:
    """Create a new user."""

    db = get_db()

    try:
        existing_user = (
            db.query(User)
            .filter(
                (User.username == username)
                | (User.email == email)
            )
            .first()
        )

        if existing_user:
            return None

        new_user = User(
            username=username,
            email=email,
            password_hash=hash_password(password),
            role=role,
        )

        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        return new_user

    finally:
        db.close()


def update_user(
    user_id: str,
    username: str,
    email: str,
    role: UserRole,
):
    db = get_db()

    try:

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            return False, "User not found."

        duplicate_username = (
            db.query(User)
            .filter(
                User.username == username,
                User.id != user_id
            )
            .first()
        )

        if duplicate_username:
            return False, "Username already exists."

        duplicate_email = (
            db.query(User)
            .filter(
                User.email == email,
                User.id != user_id
            )
            .first()
        )

        if duplicate_email:
            return False, "Email already exists."

        user.username = username
        user.email = email
        user.role = role

        db.commit()

        return True, "Updated successfully."

    finally:
        db.close()


def activate_user(user_id: str) -> bool:
    """Activate a user account."""

    db = get_db()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return False

        user.is_active = True

        db.commit()

        return True

    finally:
        db.close()


def deactivate_user(user_id: str) -> bool:
    """Deactivate a user account."""

    db = get_db()

    try:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            return False

        user.is_active = False

        db.commit()

        return True

    finally:
        db.close()


def delete_user(
    user_id: str,
    current_user_id: str,
):
    db = get_db()

    try:

        user = (
            db.query(User)
            .filter(User.id == user_id)
            .first()
        )

        if not user:
            return False, "User not found."

        if user.id == current_user_id:
            return False, "You cannot delete yourself."

        if user.role == UserRole.ADMIN:

            admin_count = (
                db.query(User)
                .filter(User.role == UserRole.ADMIN)
                .count()
            )

            if admin_count <= 1:
                return False, "Cannot delete the last admin."

        db.delete(user)
        db.commit()

        return True, "User deleted."

    finally:
        db.close()