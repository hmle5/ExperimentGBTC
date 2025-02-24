# Calling the necessary libraries
from flask import (
    Flask,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    send_file,
)
import json
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
import pandas as pd
import random
import uuid
from datetime import datetime


from .utilis import get_client_ip, get_user_agent

# Initialize the Flask app
app = Flask(__name__)
# Set the secret key for the app
app.secret_key = "supersecretkey"

# Set up the database
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///responses.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

migrate = Migrate(app, db)


# Define the UserConsent model
class UserConsent(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    consent_id = db.Column(db.String(100), unique=True, nullable=False)
    ip_address = db.Column(db.String(50), nullable=False)
    user_agent = db.Column(db.String(200), nullable=False)
    consent_given = db.Column(db.Boolean, default=False, nullable=False)


# Landing page
@app.route("/", methods=["GET"])
def consent():
    ip = get_client_ip()
    user_agent = get_user_agent()
    consent_record = UserConsent.query.filter_by(
        ip_address=ip, user_agent=user_agent
    ).first()

    if consent_record and consent_record.consent_given:
        return redirect(url_for("index"))
    return render_template("consent.html")


# Consent page
@app.route("/give_consent", methods=["POST"])
def give_consent():
    consent_status = request.form.get("consent")
    if consent_status == "accepted":
        ip = get_client_ip()
        user_agent = get_user_agent()
        consent_id = str(uuid.uuid4())
        consent_record = UserConsent(
            consent_id=consent_id,
            ip_address=ip,
            user_agent=user_agent,
            consent_given=True,
        )
        db.session.add(consent_record)
        db.session.commit()
        session["consent_id"] = consent_id
        return redirect(url_for("index"))
    elif consent_status == "denied":
        return redirect(url_for("exit"))
    else:
        flash("Please select an option to proceed.")
        return redirect(url_for("consent"))


# Privacy policy page
@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
