from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, Response
import pandas as pd
import io
from flask import Response as FlaskResponse
from functools import wraps  # Use wraps to preserve function metadata
import statistics

admin_bp = Blueprint("admin_bp", __name__)


def admin_required(func):
    """
    Ensures only logged-in admins can access the dashboard.
    Fixes function overwrite issue using `wraps`.
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        if "admin" not in session:
            flash("Unauthorized access! Please log in as admin.", "error")
            return redirect(url_for("admin_bp.admin_login"))
        return func(*args, **kwargs)

    return wrapper


@admin_bp.route("/admin", methods=["GET"])
@admin_required
def admin_dashboard():
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 10))

    paginated = Response.query.paginate(page=page, per_page=per_page, error_out=False)
    all_responses = Response.query.all()

    # Compute stats
    success_probs = [
        r.success_prob for r in all_responses if r.success_prob is not None
    ]
    avg_success = round(statistics.mean(success_probs), 2) if success_probs else None
    total_completed = sum(1 for r in all_responses if r.completed)

    # Serialize only paginated items for chart JS
    def serialize_response(r):
        return {
            "participant_id": r.participant_id,
            "success_prob": r.success_prob,
            "failure_prob": r.failure_prob,
            "voyagemind_investment": r.voyagemind_investment,
            "expected_return": r.expected_return,
            "completed": r.completed,
            "start_time": r.start_time.isoformat() if r.start_time else None,
            "end_time": r.end_time.isoformat() if r.end_time else None,
        }

    serialized_responses = [serialize_response(r) for r in paginated.items]

    return render_template(
        "admin_dashboard.html",
        responses=paginated.items,
        serialized_responses=serialized_responses,
        page=page,
        per_page=per_page,
        total=paginated.total,
        avg_success=avg_success,
        total_completed=total_completed,
    )


@admin_bp.route("/admin/export_excel", methods=["GET"])
@admin_required
def export_excel():
    responses = Response.query.all()
    data = [
        {
            "Participant ID": r.participant_id,
            "Success Probability": r.success_prob,
            "Failure Probability": r.failure_prob,
            "Investment Amount": r.voyagemind_investment,
            "Expected Return": r.expected_return,
            "Completed": r.completed,
            "Start Time": r.start_time,
            "End Time": r.end_time,
            "Story Type": r.story_type,
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
    """
    Exports survey data as a CSV file.
    """
    responses = Response.query.all()
    data = []

    for resp in responses:
        data.append(
            {
                "Participant ID": resp.participant_id,
                "Success Probability": resp.success_probability,
                "Failure Probability": resp.failure_probability,
                "Investment Amount": resp.investment_amount,
                "Expected Return": resp.expected_return,
                "Completed Index": resp.completed_index,
                "Completed Instructions": resp.completed_instructions,
                "Completed Survey": resp.completed_survey,
                "Start Time": resp.start_time,
                "End Time": resp.end_time,
            }
        )

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
    """
    Admin login page.
    """
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        if username == "admin" and password == "securepassword":  # Change credentials
            session["admin"] = True
            return redirect(url_for("admin_bp.admin_dashboard"))
        else:
            flash("Invalid credentials!", "error")

    return render_template("admin_login.html")


@admin_bp.route("/admin/logout")
def admin_logout():
    """
    Logs out the admin.
    """
    session.pop("admin", None)
    flash("Logged out successfully!", "success")
    return redirect(url_for("admin_bp.admin_login"))
