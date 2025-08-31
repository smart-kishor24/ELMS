from flask_wtf import FlaskForm
from wtforms import SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired

class ApproveLeaveForm(FlaskForm):
    status = SelectField(
        "Status",
        choices=[("Approved", "Approve"), ("Rejected", "Reject")],
        validators=[DataRequired()]
    )
    comment = TextAreaField("Comment")
    submit = SubmitField("Submit Decision")