from flask import Blueprint, render_template, request, send_file, flash, redirect
from flask_login import login_required, current_user
from .utils import generate_report_df
from weasyprint import HTML
import io

reports_bp = Blueprint("reports", __name__, url_prefix="/reports")

@reports_bp.route("/generate", methods=["GET", "POST"])
@login_required
def generate():
    if current_user.role != "Admin":
        flash("Access denied", "danger")
        return redirect("/")

    if request.method == "POST":
        report_type = request.form.get("type")  # CSV or PDF
        df = generate_report_df()  # Can add filters here
        if report_type == "CSV":
            return send_file(
                io.BytesIO(df.to_csv(index=False).encode()),
                mimetype="text/csv",
                download_name="leave_report.csv",
                as_attachment=True
            )
        elif report_type == "PDF":
            html = render_template("reports/report.html", data=df.to_dict(orient="records"))
            pdf_file = HTML(string=html).write_pdf()
            return send_file(io.BytesIO(pdf_file), mimetype="application/pdf", download_name="leave_report.pdf", as_attachment=True)

    return render_template("reports/generate.html")