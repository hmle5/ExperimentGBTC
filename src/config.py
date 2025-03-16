class Config:
    SECRET_KEY = "supersecretkey"  # In production, use an environment variable
    SQLALCHEMY_DATABASE_URI = "sqlite:///responses.db"
    SQLALCHEMY_TRACK_MODIFICATIONS = False
