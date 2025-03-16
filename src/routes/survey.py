from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import random
from datetime import datetime
from models import db, Response
from utilis import generate_unique_participant_id

survey_bp = Blueprint("survey_bp", __name__)  # Ensure the correct Blueprint name

# Dummy startup dataset for randomized selection
startups = [
    {
        "name": "TechSpark",
        "industry": "AI",
        "pitch": "An AI-driven platform optimizing e-commerce logistics.",
        "promised_return": 200,
        "founder": "Female",
    },
    {
        "name": "GreenEnergy",
        "industry": "Sustainable Energy",
        "pitch": "Affordable solar panels for rural areas.",
        "promised_return": 180,
        "founder": "Male",
    },
    {
        "name": "MediFlow",
        "industry": "HealthTech",
        "pitch": "A telemedicine platform for remote patients.",
        "promised_return": 220,
        "founder": "Female",
    },
    {
        "name": "AutoDrive",
        "industry": "Autonomous Vehicles",
        "pitch": "Self-driving delivery vehicles.",
        "promised_return": 190,
        "founder": "Male",
    },
]


@survey_bp.route("/survey", methods=["GET"])
def survey():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    selected_startup = random.choice(startups)  # Randomly assign a startup

    return render_template(
        "survey.html",
        startup_name=selected_startup["name"],
        founder_gender=selected_startup["founder"],
        startup_industry=selected_startup["industry"],
        startup_pitch=selected_startup["pitch"],
        promised_return=selected_startup["promised_return"],
    )


@survey_bp.route("/submit_survey", methods=["POST"])
def submit_survey():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    success_probability = request.form.get("success_probability", type=float)
    failure_probability = request.form.get("failure_probability", type=float)
    investment_amount = request.form.get("investment_amount", type=float)

    if (
        success_probability is None
        or failure_probability is None
        or investment_amount is None
    ):
        flash("Please complete all fields before submitting.", "error")
        return redirect(url_for("survey_bp.survey"))

    expected_return = (
        success_probability * 2
    ) - failure_probability  # Example calculation

    # Save response to database
    response_record = Response.query.filter_by(
        participant_id=session["participant_id"]
    ).first()
    if response_record:
        response_record.completed = True
        response_record.end_time = datetime.utcnow()
        db.session.commit()

    flash("Your response has been recorded. Thank you!", "success")
    return redirect(url_for("survey_bp.thank_you"))


@survey_bp.route("/thank_you")
def thank_you():
    return (
        "<h1>Thank you for participating!</h1><p>Your response has been recorded.</p>"
    )
