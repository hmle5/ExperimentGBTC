from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class UserConsent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consent_id = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    user_agent = db.Column(db.String(200), nullable=False)
    consent_given = db.Column(db.Boolean, default=False, nullable=False)
    date_given = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)


class Response(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consent_id = db.Column(
        db.String(100),
        db.ForeignKey("user_consent.consent_id"),
        nullable=False,
        unique=True,
    )
    participant_id = db.Column(db.String(100), unique=True, nullable=False)
    completed = db.Column(db.Boolean, default=False, nullable=False)
    start_time = db.Column(db.DateTime, nullable=True)
    end_time = db.Column(db.DateTime, nullable=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    date_updated = db.Column(
        db.DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    # Relationship for easy access to UserConsent
    user_consent = db.relationship("UserConsent", backref="responses")

    # Index for faster queries
    __table_args__ = (db.Index("idx_response_consent_id", "consent_id"),)
