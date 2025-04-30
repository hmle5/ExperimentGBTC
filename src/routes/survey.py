from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash,
    get_flashed_messages,
)

from decimal import Decimal, ROUND_HALF_UP, InvalidOperation

import random
from datetime import datetime
from models import db, Response, StartupSetAssignment
from utilis import (
    get_unused_story,
    mark_story_as_used,
    generate_news_story_file,
    HOLMES_ARTICLE,
    CONTROL_ARTICLE,
    # generate_startup_file,
    # get_unused_startup,
    # mark_startup_as_used,
    generate_startup_sets,
    mark_startup_set_as_used,
)
from models import db, Response
import time
import json
import os

survey_bp = Blueprint("survey_bp", __name__)  # Ensure the correct Blueprint name


# Dummy startup dataset for randomized selection
@survey_bp.route("/instructions", methods=["GET"])
def instructions():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))  # Ensure only valid participants proceed

    return render_template("instructions.html")


@survey_bp.route("/educating", methods=["GET", "POST"])
def educating():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))  # Ensure only valid participants proceed

    return render_template("educating.html")


@survey_bp.route("/phase_control", methods=["GET", "POST"])
def phase_control():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))  # Ensure only valid participants proceed

    return render_template("phase_control.html")


@survey_bp.route("/news_info", methods=["GET", "POST"])
def news_info():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    generate_news_story_file()

    if request.method == "POST":
        user_answer = request.form.get("news_answer")
        story_type = request.form.get("story_type")
        unique_code = request.form.get("unique_code")

        if not user_answer:
            flash("Please select an answer before proceeding.", "error")
            return redirect(url_for("survey_bp.news_info"))

        # Load article based on story_type to get the correct answer
        article_data = HOLMES_ARTICLE if story_type == "holmes" else CONTROL_ARTICLE
        correct_answer = article_data["correct_answer"]

        is_correct = user_answer == correct_answer

        if not is_correct:
            flash("Incorrect answer. Try again.", "error")
            return redirect(url_for("survey_bp.news_info"))

        mark_story_as_used(unique_code)

        response.unique_code = unique_code
        response.story_type = story_type
        response.user_answer = user_answer
        response.is_correct = is_correct
        response.last_page_viewed = "news_info"
        db.session.commit()
        get_flashed_messages()  # <--- THIS clears any old messages BEFORE redirect

        return redirect(url_for("survey_bp.investment"))

    # === GET method ===
    story_entry = get_unused_story()
    if not story_entry:
        flash("All available stories have been used. Survey is closed.", "error")
        return redirect(url_for("main.index"))

    article_data = (
        HOLMES_ARTICLE if story_entry["story"] == "holmes" else CONTROL_ARTICLE
    )
    correct_answer = article_data["correct_answer"]
    shuffled_options = article_data["options"].copy()
    # random.shuffle(shuffled_options)

    return render_template(
        "news_info.html",
        news_title=article_data["title"],
        news_content=article_data["content"],
        news_source=article_data["source"],
        question=article_data["question"],
        options=shuffled_options,
        unique_code=story_entry["code"],
        story_type=story_entry["story"],
        correct_answer=correct_answer,
    )


@survey_bp.route("/investment", methods=["GET", "POST"])
def investment():
    print("Debug: participant_id in session:", session.get("participant_id"))

    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    STARTUP_JSON_PATH = "startup_data.json"

    # === POST: form submission ===
    if request.method == "POST":
        set_code = session.get("startup_set_code")
        startups = session.get("startups")
        start_time = session.get("startup_set_start_time")

        if not set_code or not start_time or not startups:
            flash("Session expired. Please restart the task.", "error")
            return redirect(url_for("main.index"))

        time_spent = time.time() - start_time
        investments = {}
        total_investment = 0

        for startup in startups:
            startup_name = startup["Startup_name"]
            field_name = f"investment_{startup_name}"
            amount_str = request.form.get(field_name)

            if amount_str is None:
                flash("Missing investment amount.", "error")
                return render_template("investment_multi.html", startups=startups)

            try:
                amount = int(round(float(amount_str)))
            except (ValueError, TypeError):
                flash("Invalid amount entered.", "error")
                return render_template("investment_multi.html", startups=startups)

            # try:
            #     amount = int(
            #         Decimal(amount_str).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
            #     )
            #     print(
            #         f"{startup_name} → raw: {amount_str} → Decimal: {Decimal(amount_str)} → final: {amount}"
            #     )

            # except (InvalidOperation, ValueError, TypeError):
            #     flash("Invalid amount entered.", "error")
            #     return render_template("investment_multi.html", startups=startups)

            if not (0 <= amount <= 300000):
                flash("Each amount must be between 0 and 300,000.", "error")
                return render_template("investment_multi.html", startups=startups)

            investments[startup_name] = amount
            total_investment += amount

        if total_investment != 300000:
            flash(
                f"Total investment must be exactly $300,000. Your total: ${total_investment:,}.",
                "error",
            )
            return render_template("investment_multi.html", startups=startups)

        # Save to database
        if response:
            response.startup_code = set_code
            response.startup_investments = investments
            response.startup_investment_duration = time_spent
            db.session.commit()
        else:
            flash("Error saving investments.", "error")
            return redirect(url_for("main.index"))

        # Mark as used in DB
        assignment = StartupSetAssignment.query.filter_by(
            startup_set_code=set_code
        ).first()
        if assignment:
            assignment.used = True
            assignment.duration_seconds = time_spent
            db.session.commit()

        # Now permanently mark JSON set as used
        mark_startup_set_as_used(set_code)

        # Clear session so next GET loads a fresh set
        session.pop("startups", None)
        session.pop("startup_set_code", None)
        session.pop("startup_set_start_time", None)

        return redirect(url_for("survey_bp.investment_approach"))

    # === GET: show form ===
    if "startups" not in session:
        # Load new startup set
        with open(STARTUP_JSON_PATH, "r") as file:
            startup_data = json.load(file)

        unused_sets = [item for item in startup_data if not item["used"]]

        if not unused_sets:
            flash("No unused startup sets available.", "error")
            return redirect(url_for("main.index"))

        selected_set = unused_sets[0]
        session["startups"] = selected_set["startups"]
        session["startup_set_code"] = selected_set["code"]
        session["startup_set_start_time"] = time.time()

        selected_set["used"] = True  # temporary flag only
        with open(STARTUP_JSON_PATH, "w") as file:
            json.dump(startup_data, file)

        # Create or update assignment
        assignment = StartupSetAssignment.query.filter_by(
            participant_id=participant_id
        ).first()
        if not assignment:
            assignment = StartupSetAssignment(
                participant_id=participant_id,
                startup_set_code=selected_set["code"],
                used=True,
                duration_seconds=None,
            )
            db.session.add(assignment)
        else:
            assignment.startup_set_code = selected_set["code"]
            assignment.used = True
            assignment.duration_seconds = None
        db.session.commit()

    # else: session already has the set (retry after failed POST)
    startups = session["startups"]

    print("Debug: session['startup_set_code']:", session.get("startup_set_code"))
    print("Debug: session['startups']:", startups)
    print(
        "Debug: session['startup_set_start_time']:",
        session.get("startup_set_start_time"),
    )

    return render_template("investment_multi.html", startups=startups)


# @survey_bp.route("/investment_reflecting", methods=["GET", "POST"])
# def investment_reflecting():
#     if "participant_id" not in session:
#         return redirect(url_for("main.index"))

#     participant_id = session["participant_id"]
#     response = Response.query.filter_by(participant_id=participant_id).first()

#     if request.method == "POST":
#         startup_choices = request.form.getlist("startup_factors")
#         founder_choices = request.form.getlist("founder_factors")

#         if not startup_choices or not founder_choices:
#             flash(
#                 "Please select at least one factor for both startup and founder.",
#                 "error",
#             )
#             return redirect(url_for("survey_bp.investment_reflecting"))

#         response.startup_factors = ",".join(startup_choices)
#         response.founder_factors = ",".join(founder_choices)
#         response.last_page_viewed = "investment_reflecting"
#         db.session.commit()

#         return redirect(
#             url_for("survey_bp.investment_demographic")
#         )  # Replace with your next route

#     return render_template("investment_reflecting.html")


@survey_bp.route("/investment_approach", methods=["GET", "POST"])
def investment_approach():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    if request.method == "POST":
        approach_text = request.form.get("investment_approach", "").strip()

        if not approach_text or len(approach_text.split()) < 15:
            flash("Please briefly describe your investment approach.", "error")
            return redirect(url_for("survey_bp.investment_approach"))

        response.investment_approach = approach_text
        response.last_page_viewed = "investment_approach"
        db.session.commit()

        return redirect(
            url_for("survey_bp.investment_reflect_likert")
        )  # Replace with your next route

    return render_template("investment_approach.html")


@survey_bp.route("/investment_reflect_likert", methods=["GET", "POST"])
def investment_reflect_likert():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    if request.method == "POST":
        keys = [
            "industry_rating",
            "product_rating",
            "maturity_rating",
            "experience_rating",
            "innovativeness_rating",
            "integrity_rating",
        ]

        likert_data = {}
        for key in keys:
            val = request.form.get(key)
            if not val:
                flash(f"Missing response for: {key.replace('_', ' ').title()}", "error")
                return redirect(url_for("survey_bp.investment_reflect_likert"))
            likert_data[key] = int(val)

        response.likert_reflection = likert_data  # Optional if column is Text
        response.last_page_viewed = "investment_reflect_likert"
        db.session.commit()

        return redirect(url_for("survey_bp.investment_demographic"))  # Or next step

    return render_template("investment_reflect_likert.html")


@survey_bp.route("/demographic_collecting", methods=["GET", "POST"])
def investment_demographic():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    if request.method == "POST":
        gender = request.form.get("gender")
        gender_other = request.form.get("gender_other") if gender == "Other" else None

        age = request.form.get("age")

        education = request.form.get("education")
        education_other = (
            request.form.get("education_other") if education == "Other" else None
        )

        if not gender or not age or not education:
            flash("Please complete all fields before submitting.", "error")
            return redirect(url_for("survey_bp.investment_demographic"))

        if gender == "Other" and not gender_other:
            flash("Please specify your gender.", "error")
            return redirect(url_for("survey_bp.investment_demographic"))

        if education == "Other" and not education_other:
            flash("Please specify your education level.", "error")
            return redirect(url_for("survey_bp.investment_demographic"))

        try:
            age_val = int(age)
            if age_val < 10 or age_val > 120:
                flash("Please enter a valid age between 10 and 120.", "error")
                return redirect(url_for("survey_bp.investment_demographic"))
        except ValueError:
            flash("Age must be a number.", "error")
            return redirect(url_for("survey_bp.investment_demographic"))

        response.gender = gender_other if gender == "Other" else gender
        response.age = age_val
        response.education_level = (
            education_other if education == "Other" else education
        )
        response.last_page_viewed = "demographic_collecting"
        db.session.commit()

        return redirect(url_for("survey_bp.final_page"))

    return render_template("demographic.html")


@survey_bp.route("/final_page", methods=["GET", "POST"])
def final_page():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    # if not response or not response.unique_code or not response.startup_code:
    #     flash("Missing completion code data.", "error")
    #     return redirect(url_for("main.index"))
    # Get startup code from StartupSetAssignment instead of response.startup_code
    assignment = StartupSetAssignment.query.filter_by(
        participant_id=participant_id
    ).first()

    if (
        not response
        or not response.unique_code
        or not assignment
        or not assignment.startup_set_code
    ):
        flash("Missing completion code data.", "error")
        return redirect(url_for("main.index"))

    expected_code = f"{response.unique_code}{assignment.startup_set_code}"

    if request.method == "POST":
        mturk_id = request.form.get("mturk_id", "").strip()
        user_code = request.form.get("completion_code", "").strip().upper()

        if not mturk_id or not user_code:
            flash("Please fill in all required fields.", "error")
            return redirect(url_for("survey_bp.final_page"))

        if user_code != expected_code:
            flash(
                "The code you entered is incorrect. Please check and try again.",
                "error",
            )
            return redirect(url_for("survey_bp.final_page"))

        # Save to DB
        response.mturk_id = mturk_id
        response.completion_code = user_code
        response.last_page_viewed = "final_page"
        db.session.commit()

        # Store for thank-you page
        session["completion_code"] = user_code
        session["mturk_id"] = mturk_id

        return redirect(url_for("survey_bp.thank_you"))

    return render_template("final_page.html", expected_code=expected_code)


@survey_bp.route("/thank_you")
def thank_you():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    mturk_id = session.get("mturk_id", "")
    completion_code = session.get("completion_code", "")

    # Mark survey as completed
    response.completed = True
    db.session.commit()

    return render_template(
        "thank_you.html", mturk_id=mturk_id, completion_code=completion_code
    )
