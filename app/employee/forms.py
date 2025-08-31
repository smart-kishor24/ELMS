from flask_wtf import FlaskForm
from wtforms import StringField, DateField, SelectField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, ValidationError
from datetime import date
from ..models import LeaveRequest
from flask_login import current_user
class EmptyForm(FlaskForm):
    pass

class LeaveForm(FlaskForm):
    start_date = DateField("Start Date", validators=[DataRequired()])
    end_date = DateField("End Date", validators=[DataRequired()])
    leave_type = SelectField("Leave Type", choices=[("Sick", "Sick"), ("Casual", "Casual")])
    reason = TextAreaField("Reason")
    submit = SubmitField("Apply")

    def validate_end_date(self, field):
        if field.data < self.start_date.data:
            raise ValidationError("End date cannot be before start date.")

    def validate_start_date(self, field):
        # Check overlapping leaves
        if LeaveRequest.overlaps(current_user.id, self.start_date.data, self.end_date.data):
            raise ValidationError("This leave overlaps with an existing leave.")

class LeaveApplyForm(FlaskForm):
    start_date = DateField("Start Date", validators=[DataRequired()], format="%Y-%m-%d")
    end_date = DateField("End Date", validators=[DataRequired()], format="%Y-%m-%d")
    leave_type = SelectField("Leave Type", choices=[("Sick", "Sick"), ("Casual", "Casual"), ("Earned", "Earned")], validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired()])
    submit = SubmitField("Apply")

    def validate_end_date(self, field):
        if self.start_date.data and field.data < self.start_date.data:
            raise ValidationError("End date cannot be before start date.")
        if self.start_date.data < date.today():
            # optionally disallow past-start date
            raise ValidationError("Start date cannot be in the past.")


class LeaveEditForm(FlaskForm):
    start_date = DateField("Start Date", validators=[DataRequired()], format="%Y-%m-%d")
    end_date = DateField("End Date", validators=[DataRequired()], format="%Y-%m-%d")
    leave_type = SelectField("Leave Type", choices=[("Sick", "Sick"), ("Casual", "Casual"), ("Earned", "Earned")], validators=[DataRequired()])
    reason = TextAreaField("Reason", validators=[DataRequired()])
    submit = SubmitField("Update")

    def validate_end_date(self, field):
        if self.start_date.data and field.data < self.start_date.data:
            raise ValidationError("End date cannot be before start date.")