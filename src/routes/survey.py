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

    # if response.last_page_viewed != "phasing":
    #     return redirect(url_for(f"survey_bp.{response.last_page_viewed}"))

    # Ensure the news story file is available before selecting a story
    generate_news_story_file()

    if request.method == "POST":
        user_answer = request.form.get("news_answer")
        entered_code = request.form.get("user_code")
        correct_code = request.form.get("unique_code")
        story_type = request.form.get("story_type")

        if not user_answer or not entered_code:
            flash(
                "Please enter the unique code and select an answer before proceeding.",
                "error",
            )
            return redirect(url_for("survey_bp.news_info"))

        correct_answer = (
            HOLMES_ARTICLE["correct_answer"]
            if story_type == "holmes"
            else MYSTICETES_ARTICLE["correct_answer"]
        )
        is_correct = user_answer == correct_answer

        if not is_correct:
            flash("Incorrect answer. Try again.", "error")
            return redirect(url_for("survey_bp.news_info"))

        if entered_code != correct_code:
            flash(
                "Incorrect code entered. Please enter the correct code to proceed.",
                "error",
            )
            return redirect(url_for("survey_bp.news_info"))

        # Mark story as used only AFTER user answers correctly
        mark_story_as_used(correct_code)

        # Store selection in database
        response.unique_code = correct_code
        response.story_type = story_type
        response.user_answer = user_answer
        response.is_correct = is_correct
        response.last_page_viewed = "news_info"
        db.session.commit()

        return redirect(url_for("survey_bp.investment"))

    # Fetch a random unused story
    story_entry = get_unused_story()
    if not story_entry:
        flash("All available stories have been used. Survey is closed.", "error")
        return redirect(url_for("main.index"))

    article_data = (
        HOLMES_ARTICLE if story_entry["story"] == "holmes" else MYSTICETES_ARTICLE
    )

    # **Properly shuffle options**
    shuffled_options = article_data["options"].copy()
    random.shuffle(shuffled_options)

    return render_template(
        "news_info.html",
        news_title=article_data["title"],
        news_content=article_data["content"],
        news_source=article_data["source"],
        question=article_data["question"],
        options=shuffled_options,  # Now shuffled properly
        unique_code=story_entry["code"],
        story_type=story_entry["story"],
        correct_answer=article_data["correct_answer"],
    )
