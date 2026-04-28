"""
database/models.py
------------------
Defines SQLAlchemy ORM models for the Food Wastage Management System.
Tables: User, FoodListing, FoodRequest
"""

from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(UserMixin, db.Model):
    """Represents a registered user (donor or requester)."""
    __tablename__ = "users"

    id            = db.Column(db.Integer, primary_key=True)
    name          = db.Column(db.String(120), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    phone         = db.Column(db.String(20), nullable=True)
    location      = db.Column(db.String(200), nullable=True)
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    donations = db.relationship("FoodListing", backref="donor", lazy=True)
    requests  = db.relationship("FoodRequest",  backref="requester", lazy=True)

    def set_password(self, password: str):
        """Hash and store password using pbkdf2:sha256.

        Werkzeug >= 2.3 defaults to scrypt, which requires OpenSSL scrypt
        support compiled into Python. Python 3.9 builds often lack this,
        causing: AttributeError: module 'hashlib' has no attribute 'scrypt'.
        Explicitly specifying pbkdf2:sha256 works on all Python versions.
        """
        self.password_hash = generate_password_hash(
            password,
            method="pbkdf2:sha256",
            salt_length=16,
        )

    def check_password(self, password: str) -> bool:
        """Verify a plaintext password against stored hash."""
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"


class FoodListing(db.Model):
    """Represents a food donation listing."""
    __tablename__ = "food_listings"

    id           = db.Column(db.Integer, primary_key=True)
    food_name    = db.Column(db.String(150), nullable=False)
    quantity     = db.Column(db.String(100), nullable=False)   # e.g. "5 kg", "20 plates"
    location     = db.Column(db.String(250), nullable=False)
    description  = db.Column(db.Text, nullable=True)
    category     = db.Column(db.String(80),  nullable=True)    # e.g. Cooked, Raw, Packaged
    expiry_time  = db.Column(db.DateTime, nullable=False)
    status       = db.Column(db.String(20),  default="available")  # available | claimed | expired
    created_at   = db.Column(db.DateTime,  default=datetime.utcnow)
    donor_id     = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    # One food listing can have many requests
    requests = db.relationship("FoodRequest", backref="food_listing", lazy=True)

    @property
    def is_expired(self) -> bool:
        return datetime.utcnow() > self.expiry_time

    def __repr__(self):
        return f"<FoodListing {self.food_name} [{self.status}]>"


class FoodRequest(db.Model):
    """Represents a request/claim on a food listing."""
    __tablename__ = "food_requests"

    id             = db.Column(db.Integer, primary_key=True)
    food_id        = db.Column(db.Integer, db.ForeignKey("food_listings.id"), nullable=False)
    requester_id   = db.Column(db.Integer, db.ForeignKey("users.id"),         nullable=False)
    message        = db.Column(db.Text,    nullable=True)     # optional note from requester
    status         = db.Column(db.String(20), default="pending")  # pending | approved | rejected
    requested_at   = db.Column(db.DateTime,   default=datetime.utcnow)

    def __repr__(self):
        return f"<FoodRequest food={self.food_id} by user={self.requester_id} [{self.status}]>"
