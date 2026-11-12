"""Database models: User, Drill, PracticePlan and PlanDrill.

Relationships
    User 1 --- * Drill
    User 1 --- * PracticePlan
    PracticePlan * --- * Drill  (through PlanDrill, which also stores the
                                 order, minutes and notes of each drill in a plan)
"""

import re
from datetime import date, datetime, timezone

from sqlalchemy import CheckConstraint
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import validates

from extensions import bcrypt, db

CATEGORIES = [
    "Warm-up", "Serving", "Passing", "Setting", "Hitting",
    "Blocking", "Defense", "Conditioning", "Team Play",
]
LEVELS = ["Beginner", "Intermediate", "Advanced"]

MIN_MINUTES = 1
MAX_MINUTES = 180


def utcnow():
    return datetime.now(timezone.utc)


def clean_text(value, field, max_length, required=False):
    """Trim a text value and check its length. Returns None for empty optional text."""
    if value is None:
        value = ""
    if not isinstance(value, str):
        raise ValueError(f"{field} must be text.")
    value = value.strip()
    if required and not value:
        raise ValueError(f"{field} is required.")
    if len(value) > max_length:
        raise ValueError(f"{field} must be {max_length} characters or fewer.")
    return value or None


def clean_minutes(value, field, low=MIN_MINUTES, high=MAX_MINUTES):
    """Make sure a number of minutes is a whole number in range."""
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise ValueError(f"{field} must be a whole number.")
    try:
        number = int(value)
    except ValueError:
        raise ValueError(f"{field} must be a whole number.") from None
    if not low <= number <= high:
        raise ValueError(f"{field} must be between {low} and {high}.")
    return number


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(30), unique=True, nullable=False)
    _password_hash = db.Column("password_hash", db.String(128), nullable=False)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    drills = db.relationship("Drill", back_populates="user", cascade="all, delete-orphan")
    plans = db.relationship("PracticePlan", back_populates="user", cascade="all, delete-orphan")

    @hybrid_property
    def password_hash(self):
        # Nobody should ever read a password hash back out of the model.
        raise AttributeError("Password hashes cannot be viewed.")

    @password_hash.setter
    def password_hash(self, password):
        if not isinstance(password, str) or len(password) < 8:
            raise ValueError("Password must be at least 8 characters.")
        if len(password) > 128:
            raise ValueError("Password must be 128 characters or fewer.")
        self._password_hash = bcrypt.generate_password_hash(password).decode("utf-8")

    def authenticate(self, password):
        return bcrypt.check_password_hash(self._password_hash, password)

    @validates("username")
    def validate_username(self, key, value):
        value = clean_text(value, "Username", 30, required=True)
        if not re.fullmatch(r"[A-Za-z0-9_]{3,30}", value):
            raise ValueError("Username must be 3-30 letters, numbers or underscores.")
        return value

    def to_dict(self):
        return {"id": self.id, "username": self.username}


class Drill(db.Model):
    __tablename__ = "drills"
    __table_args__ = (
        CheckConstraint("default_minutes BETWEEN 1 AND 180", name="ck_drill_minutes"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    name = db.Column(db.String(80), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(20), nullable=False, default="Warm-up")
    skill_level = db.Column(db.String(20), nullable=False, default="Beginner")
    default_minutes = db.Column(db.Integer, nullable=False, default=10)
    equipment = db.Column(db.String(120))
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    user = db.relationship("User", back_populates="drills")
    # Deleting a drill also removes it from any plan that used it.
    plan_items = db.relationship("PlanDrill", back_populates="drill", cascade="all, delete-orphan")

    @validates("name")
    def validate_name(self, key, value):
        return clean_text(value, "Name", 80, required=True)

    @validates("description")
    def validate_description(self, key, value):
        return clean_text(value, "Description", 1000)

    @validates("equipment")
    def validate_equipment(self, key, value):
        return clean_text(value, "Equipment", 120)

    @validates("category")
    def validate_category(self, key, value):
        if value not in CATEGORIES:
            raise ValueError(f"Category must be one of: {', '.join(CATEGORIES)}.")
        return value

    @validates("skill_level")
    def validate_level(self, key, value):
        if value not in LEVELS:
            raise ValueError(f"Skill level must be one of: {', '.join(LEVELS)}.")
        return value

    @validates("default_minutes")
    def validate_minutes(self, key, value):
        return clean_minutes(value, "Default minutes")

    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description or "",
            "category": self.category,
            "skill_level": self.skill_level,
            "default_minutes": self.default_minutes,
            "equipment": self.equipment or "",
        }


class PracticePlan(db.Model):
    __tablename__ = "practice_plans"
    __table_args__ = (
        CheckConstraint("target_minutes BETWEEN 15 AND 300", name="ck_plan_target"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    focus = db.Column(db.String(200))
    practice_date = db.Column(db.Date)
    target_minutes = db.Column(db.Integer, nullable=False, default=90)
    notes = db.Column(db.Text)
    created_at = db.Column(db.DateTime(timezone=True), default=utcnow)

    user = db.relationship("User", back_populates="plans")
    items = db.relationship(
        "PlanDrill",
        back_populates="plan",
        cascade="all, delete-orphan",
        order_by="PlanDrill.position",
    )

    @validates("title")
    def validate_title(self, key, value):
        return clean_text(value, "Title", 100, required=True)

    @validates("focus")
    def validate_focus(self, key, value):
        return clean_text(value, "Focus", 200)

    @validates("notes")
    def validate_notes(self, key, value):
        return clean_text(value, "Notes", 2000)

    @validates("target_minutes")
    def validate_target(self, key, value):
        return clean_minutes(value, "Target minutes", low=15, high=300)

    @validates("practice_date")
    def validate_date(self, key, value):
        if value in (None, ""):
            return None
        if isinstance(value, date):
            return value
        try:
            return date.fromisoformat(value)
        except (TypeError, ValueError):
            raise ValueError("Practice date must look like YYYY-MM-DD.") from None

    @property
    def total_minutes(self):
        return sum(item.minutes for item in self.items)

    def to_dict(self, include_items=False):
        data = {
            "id": self.id,
            "title": self.title,
            "focus": self.focus or "",
            "practice_date": self.practice_date.isoformat() if self.practice_date else None,
            "target_minutes": self.target_minutes,
            "notes": self.notes or "",
            "item_count": len(self.items),
            "total_minutes": self.total_minutes,
        }
        if include_items:
            data["items"] = [item.to_dict() for item in self.items]
        return data


class PlanDrill(db.Model):
    """One drill inside one plan, with its own order, minutes and notes."""

    __tablename__ = "plan_drills"
    __table_args__ = (
        CheckConstraint("minutes BETWEEN 1 AND 180", name="ck_item_minutes"),
    )

    id = db.Column(db.Integer, primary_key=True)
    plan_id = db.Column(db.Integer, db.ForeignKey("practice_plans.id"), nullable=False)
    drill_id = db.Column(db.Integer, db.ForeignKey("drills.id"), nullable=False)
    position = db.Column(db.Integer, nullable=False, default=1)
    minutes = db.Column(db.Integer, nullable=False, default=10)
    notes = db.Column(db.String(300))

    plan = db.relationship("PracticePlan", back_populates="items")
    drill = db.relationship("Drill", back_populates="plan_items")

    @validates("minutes")
    def validate_minutes(self, key, value):
        return clean_minutes(value, "Minutes")

    @validates("notes")
    def validate_notes(self, key, value):
        return clean_text(value, "Notes", 300)

    def to_dict(self):
        return {
            "id": self.id,
            "position": self.position,
            "minutes": self.minutes,
            "notes": self.notes or "",
            "drill": {
                "id": self.drill.id,
                "name": self.drill.name,
                "category": self.drill.category,
                "skill_level": self.drill.skill_level,
            },
        }
