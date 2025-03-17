import uuid


class Config:
    SECRET_KEY = uuid.uuid4().hex
    # In production, use an environment variable
    SQLALCHEMY_DATABASE_URI = "sqlite:///responses.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
