from flask import Blueprint, render_template, request, session, redirect, url_for, flash
from models import db, Response
import pandas as pd
import io
from flask import Response as FlaskResponse
from functools import wraps  # Use wraps to preserve function metadata

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
    """
    Displays survey responses and progress.
    """
    responses = Response.query.all()
    return render_template("admin_dashboard.html", responses=responses)


@admin_bp.route("/admin/export", methods=["GET"])
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
