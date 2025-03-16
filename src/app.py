from flask import Flask
from flask_migrate import Migrate
from models import db
from routes.consent import main_bp  # import blueprint(s)
from routes.survey import survey_bp  # Import survey blueprint
from routes.admin import admin_bp  # Import the admin blueprint


def create_app():
    app = Flask(__name__)
    app.config.from_object("config.Config")  # load configuration from config.py

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(survey_bp)
    app.register_blueprint(admin_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()  # Create tables if they don't exist
    app.run(debug=True)
