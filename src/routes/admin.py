from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, Response
import pandas as pd
import io
from flask import Response as FlaskResponse
from functools import wraps
import statistics

admin_bp = Blueprint("admin_bp", __name__)


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            flash("Unauthorized access! Please log in as admin.", "error")
            return redirect(url_for("admin_bp.admin_login"))
        return func(*args, **kwargs)

    return wrapper


# @admin_bp.route("/admin", methods=["GET"])
# @admin_required
# def admin_dashboard():
#     page = int(request.args.get("page", 1))
#     per_page = int(request.args.get("per_page", 10))

#     paginated = Response.query.paginate(page=page, per_page=per_page, error_out=False)
#     all_responses = Response.query.all()

#     durations = [
#         (r.end_time - r.start_time).total_seconds() / 60
#         for r in all_responses
#         if r.start_time and r.end_time
#     ]
#     avg_duration = round(statistics.mean(durations), 2) if durations else None
#     total_completed = sum(1 for r in all_responses if r.completed)

#     def serialize_response(r):
#         return {
#             "participant_id": r.participant_id,
#             "completed": r.completed,
#             "start_time": r.start_time.isoformat() if r.start_time else None,
#             "end_time": r.end_time.isoformat() if r.end_time else None,
#             "investment_duration": r.startup_investment_duration,
#             "age": r.age,
#             "gender": r.gender,
#         }

#     serialized_responses = [serialize_response(r) for r in paginated.items]

#     return render_template(
#         "admin_dashboard.html",
#         responses=paginated.items,
#         serialized_responses=serialized_responses,
#         page=page,
#         per_page=per_page,
#         total=paginated.total,
#         avg_duration=avg_duration,
#         total_completed=total_completed,
#     )


@admin_bp.route("/admin", methods=["GET"])
@admin_required
def admin_dashboard():
    from sqlalchemy import and_

    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))
    gender_filter = request.args.get("gender")
    education_filter = request.args.get("education_level")

    filters = []
    if gender_filter:
        filters.append(Response.gender == gender_filter)
    if education_filter:
        filters.append(Response.education_level == education_filter)

    query = Response.query.filter(and_(*filters)) if filters else Response.query
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)
    all_responses = query.all()

    # Summary stats
    durations = [
        (r.end_time - r.start_time).total_seconds() / 60
        for r in all_responses
        if r.start_time and r.end_time
    ]
    avg_duration = round(statistics.mean(durations), 2) if durations else None
    total_completed = sum(1 for r in all_responses if r.completed)

    # Charts: avg duration by gender
    from collections import defaultdict

    duration_by_gender = defaultdict(list)
    for r in all_responses:
        if r.gender and r.start_time and r.end_time:
            duration = (r.end_time - r.start_time).total_seconds() / 60
            duration_by_gender[r.gender].append(duration)

    avg_duration_by_gender = {
        g: round(statistics.mean(d), 2) for g, d in duration_by_gender.items()
    }

    return render_template(
        "admin_dashboard.html",
        responses=paginated.items,
        page=page,
        per_page=per_page,
        total=paginated.total,
        avg_duration=avg_duration,
        total_completed=total_completed,
        avg_duration_by_gender=avg_duration_by_gender,
        selected_gender=gender_filter,
        selected_education=education_filter,
    )


@admin_bp.route("/admin/export_excel", methods=["GET"])
@admin_required
def export_excel():
    responses = Response.query.all()
    data = [
        {
            "Participant ID": r.participant_id,
            "Completed": r.completed,
            "Start Time": r.start_time,
            "End Time": r.end_time,
            "Investment Duration (mins)": r.startup_investment_duration,
            "Startup Investments": r.startup_investments,
            "Investment Approach": r.investment_approach,
            "Likert Reflection": r.likert_reflection,
            "Age": r.age,
            "Gender": r.gender,
            "Education Level": r.education_level,
        }
        for r in responses
    ]

    df = pd.DataFrame(data)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        df.to_excel(writer, index=False, sheet_name="Responses")
    output.seek(0)

    return FlaskResponse(
        output,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=responses.xlsx"},
    )


@admin_bp.route("/admin/export_csv", methods=["GET"])
@admin_required
def export_csv():
    responses = Response.query.all()
    data = [
        {
            "Participant ID": r.participant_id,
            "Completed": r.completed,
            "Start Time": r.start_time,
            "End Time": r.end_time,
            "Investment Duration (mins)": r.startup_investment_duration,
            "Startup Investments": r.startup_investments,
            "Investment Approach": r.investment_approach,
            "Likert Reflection": r.likert_reflection,
            "Age": r.age,
            "Gender": r.gender,
            "Education Level": r.education_level,
        }
        for r in responses
    ]

    df = pd.DataFrame(data)
    output = io.StringIO()
    df.to_csv(output, index=False)
    output.seek(0)

    return FlaskResponse(
        output,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment;filename=survey_responses.csv"},
    )


@admin_bp.route("/admin/login", methods=["GET", "POST"])
def admin_login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "securepassword":
            session["admin"] = True
            return redirect(url_for("admin_bp.admin_dashboard"))
        else:
            flash("Invalid credentials!", "error")

    return render_template("admin_login.html")


@admin_bp.route("/admin/logout")
def admin_logout():
    session.pop("admin", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("admin_bp.admin_login"))
