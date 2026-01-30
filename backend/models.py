from datetime import datetime

from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db


class User(db.Model):
    """Application user with simple password authentication."""

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    chats = db.relationship("Chat", back_populates="user", cascade="all, delete-orphan")
    progress_updates = db.relationship(
        "Progress", back_populates="user", cascade="all, delete-orphan"
    )
    profile = db.relationship(
        "UserProfile",
        back_populates="user",
        cascade="all, delete-orphan",
        uselist=False,
        single_parent=True,
    )

    def set_password(self, raw_password: str) -> None:
        """Hash and store the provided password."""
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        """Validate a raw password against the stored hash."""
        return check_password_hash(self.password_hash, raw_password)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "created_at": self.created_at.isoformat(),
            "profile": self.profile.to_dict() if self.profile else None,
        }


class Chat(db.Model):
    """Individual chat messages between a user and Mama Akinyi."""

    __tablename__ = "chats"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    message = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(32), nullable=False)  # "user" or "assistant"
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="chats")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "message": self.message,
            "sender": self.sender,
            "timestamp": self.timestamp.isoformat(),
        }


class Progress(db.Model):
    """Milestones or learning progress entries recorded per user."""

    __tablename__ = "progress"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    milestone = db.Column(db.String(255), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="progress_updates")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "user_id": self.user_id,
            "milestone": self.milestone,
            "notes": self.notes,
            "created_at": self.created_at.isoformat(),
        }


class UserProfile(db.Model):
    """Optional metadata captured during registration."""

    __tablename__ = "user_profiles"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False, unique=True)
    full_name = db.Column(db.String(255), nullable=False)
    details = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", back_populates="profile")

    def to_dict(self) -> dict:
        return {
            "full_name": self.full_name,
            "details": self.details,
            "created_at": self.created_at.isoformat(),
        }
