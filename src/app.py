from flask import (
    Flask,
    request,
    redirect,
    url_for,
    render_template,
    session,
    send_file,
    flash,
)
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from models import db  # Import SQLAlchemy instance
import os
import random
import string
from flask_session import Session
from captcha.image import ImageCaptcha  # Import image CAPTCHA generator
from routes.consent import main_bp
from routes.survey import survey_bp
from routes.admin import admin_bp
from utilis import (
    generate_news_story_file,
    # generate_startup_file,
    generate_startup_sets,
)


def create_app():
    app = Flask(__name__)

    # # Define the allowed survey navigation flow
    # SURVEY_FLOW = [
    #     "survey_bp.instructions",
    #     "survey_bp.educating",
    #     "survey_bp.phase_control",
    #     "survey_bp.news_info",
    #     "survey_bp.investment",
    #     "survey_bp.investment_approach",
    #     "survey_bp.investment_reflect_likert",
    #     "survey_bp.demographic_collecting",
    #     "survey_bp.final_page",
    #     "survey_bp.thank_you",
    # ]

    generate_news_story_file()
    # generate_startup_file()
    generate_startup_sets()

    # Configure application securely
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "default_very_secure_key")
    app.config["SESSION_TYPE"] = "sqlalchemy"
    app.config["SESSION_SQLALCHEMY"] = db
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///responses.db"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SESSION_PERMANENT"] = False
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

    # Initialize extensions
    db.init_app(app)
    Migrate(app, db)
    Session(app)
    csrf = CSRFProtect(app)
    limiter = Limiter(get_remote_address, app=app, default_limits=["5 per minute"])


    def generate_captcha_text(length=6):
        """Generate a random CAPTCHA text with uppercase and numbers only for readability."""
        characters = string.ascii_uppercase + string.digits
        length = random.randint(5, 7)  # Randomize CAPTCHA length
        return "".join(random.choices(characters, k=length))

    @app.route("/captcha_image")
    def generate_captcha():
        """Generate a CAPTCHA image and return it securely."""
        image = ImageCaptcha(width=280, height=90)
        captcha_text = generate_captcha_text()

        # Store a hashed CAPTCHA answer instead of plaintext
        session["captcha_answer"] = captcha_text

        # Generate and save image
        captcha_path = "static/captcha.png"
        image.write(captcha_text, captcha_path)

        return send_file(captcha_path, mimetype="image/png")

    @app.route("/", methods=["GET", "POST"])
    @limiter.limit("5 per minute")  # Prevent CAPTCHA abuse
    def captcha_check():
        if request.method == "POST":
            user_input = request.form.get("captcha", "").strip().upper()

            # Validate CAPTCHA
            if user_input == session.get(
                "captcha_answer", ""
            ):  # Case-insensitive match
                session.pop("captcha_answer", None)  # Remove used CAPTCHA
                return redirect(url_for("main.consent"))
            else:
                flash("Invalid CAPTCHA. Please try again.", "error")
                return redirect(url_for("captcha_check"))

        return render_template("captcha_check.html")
    
    
    # @app.before_request
    # def prevent_back():
    #     if request.endpoint in ["static", "generate_captcha"]:
    #         return

    #     if "participant_id" in session and request.endpoint:
    #         last_page = session.get("last_page_viewed")

    #         if not last_page:
    #             return  # Allow access if no page has been tracked yet

    #         try:
    #             last_index = SURVEY_FLOW.index(last_page)
    #             current_index = SURVEY_FLOW.index(request.endpoint)
    #         except ValueError:
    #             return  # Skip check if not part of defined flow

    #         if current_index < last_index:
    #             flash("You cannot go back in the survey flow.", "error")
    #             return redirect(url_for(last_page))

            

    # Register blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(survey_bp)
    app.register_blueprint(admin_bp)

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database error: {e}")
    app.run(debug=True, host="0.0.0.0", port=5000)
