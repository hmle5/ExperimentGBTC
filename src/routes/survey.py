from flask import Blueprint, render_template, request, redirect, url_for, session, flash
import random
from datetime import datetime
from models import db, Response
from utilis import (
    get_unused_story,
    mark_story_as_used,
    generate_news_story_file,
    HOLMES_ARTICLE,
    MYSTICETES_ARTICLE,
    generate_startup_file,
    get_unused_startup,
    mark_startup_as_used,
)
from models import db, Response


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
        article_data = HOLMES_ARTICLE if story_type == "holmes" else MYSTICETES_ARTICLE
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

        return redirect(url_for("survey_bp.investment"))

    # === GET method ===
    story_entry = get_unused_story()
    if not story_entry:
        flash("All available stories have been used. Survey is closed.", "error")
        return redirect(url_for("main.index"))

    article_data = (
        HOLMES_ARTICLE if story_entry["story"] == "holmes" else MYSTICETES_ARTICLE
    )
    correct_answer = article_data["correct_answer"]
    shuffled_options = article_data["options"].copy()
    random.shuffle(shuffled_options)

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
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    # === POST: form submission ===
    if request.method == "POST":
        failure_prob = request.form.get("failure_prob")
        success_prob = request.form.get("success_prob")
        startup_code = request.form.get("startup_code")
        founder_name = request.form.get("founder_name")

        # Validate presence
        if not failure_prob or not success_prob or not founder_name:
            flash("Please complete all fields before submitting.", "error")
            return redirect(url_for("survey_bp.investment"))

        # Validate numeric + range
        try:
            failure = float(failure_prob)
            success = float(success_prob)
        except ValueError:
            flash("Please enter valid numeric values.", "error")
            return redirect(url_for("survey_bp.investment"))

        if not (0 <= failure <= 100) or not (0 <= success <= 100):
            flash("Probabilities must be between 0% and 100%.", "error")
            return redirect(url_for("survey_bp.investment"))

        if success + failure > 100:
            flash(
                "The sum of success and failure probabilities cannot exceed 100%.",
                "error",
            )
            return redirect(url_for("survey_bp.investment"))

        # Compute expected return
        promised_return = 200  # hardcoded based on current startup setup
        expected_return = success * promised_return / 100 - failure

        # Save
        mark_startup_as_used(startup_code)
        response.startup_code = startup_code
        response.founder_name = founder_name
        response.failure_prob = failure
        response.success_prob = success
        response.expected_return = expected_return
        response.last_page_viewed = "investment"
        db.session.commit()

        return redirect(url_for("survey_bp.investment_decision"))

    # === GET: show startup info ===
    generate_startup_file()
    startup_entry = get_unused_startup()
    if not startup_entry:
        flash("All start-up profiles have been used. Survey is closed.", "error")
        return redirect(url_for("main.index"))

    return render_template(
        "investment.html",
        founder=startup_entry["founder"],
        startup_code=startup_entry["code"],
    )


@survey_bp.route("/decision", methods=["GET", "POST"])
def investment_decision():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    if not response:
        flash("No response data found for participant.", "error")
        return redirect(url_for("main.index"))

    # Pull saved values from database
    success = response.success_prob or 0
    failure = response.failure_prob or 0
    promised = 200  # This can be dynamic if needed in the future
    expected_return = round(success * promised / 100 - failure, 2)

    if request.method == "POST":
        investment_amount = request.form.get("investment_amount")

        try:
            amount = float(investment_amount)
        except (ValueError, TypeError):
            flash("Please enter a valid investment amount.", "error")
            return redirect(url_for("survey_bp.investment_decision"))

        if amount < 0 or amount > 10:
            flash("Investment must be between $0 and $10.", "error")
            return redirect(url_for("survey_bp.investment_decision"))

        # Calculate expected dollar return
        projected_dollar = round(amount * expected_return / 100, 2)

        # Save to DB
        response.voyagemind_investment = amount
        response.voyagemind_dollar_return = projected_dollar
        # response.last_page_viewed = "decision"
        db.session.commit()

        return redirect(url_for("survey_bp.investment_reflecting"))

    # For GET request – display the expected return UI
    hedge_return = 35  # Static placeholder or randomized

    return render_template(
        "decision.html",
        expected_return=expected_return,
        hedge_return=hedge_return,
    )


@survey_bp.route("/investment_reflecting", methods=["GET", "POST"])
def investment_reflecting():
    if "participant_id" not in session:
        return redirect(url_for("main.index"))

    participant_id = session["participant_id"]
    response = Response.query.filter_by(participant_id=participant_id).first()

    if request.method == "POST":
        startup_choices = request.form.getlist("startup_factors")
        founder_choices = request.form.getlist("founder_factors")

        if not startup_choices or not founder_choices:
            flash(
                "Please select at least one factor for both startup and founder.",
                "error",
            )
            return redirect(url_for("survey_bp.investment_reflecting"))

        response.startup_factors = ",".join(startup_choices)
        response.founder_factors = ",".join(founder_choices)
        response.last_page_viewed = "investment_reflecting"
        db.session.commit()

        return redirect(
            url_for("survey_bp.investment_demographic")
        )  # Replace with your next route

    return render_template("investment_reflecting.html")


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

    if not response or not response.unique_code or not response.startup_code:
        flash("Missing completion code data.", "error")
        return redirect(url_for("main.index"))

    expected_code = f"{response.unique_code}{response.startup_code}"

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
