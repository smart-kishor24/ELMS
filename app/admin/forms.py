from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SelectField, SubmitField
from wtforms.validators import DataRequired, Email, Length, Optional

class DeleteForm(FlaskForm):
    pass 
class EmptyForm(FlaskForm):
    pass

class CreateUserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired(), Length(min=6)])
    role = SelectField("Role", choices=[("Admin", "Admin"), ("Manager", "Manager"), ("Employee", "Employee")])
    submit = SubmitField("Create User")

class ReportForm(FlaskForm):
    month = StringField("Month (YYYY-MM)", validators=[DataRequired()])
    submit = SubmitField("Generate Report")


class EditUserForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[Optional()])
    role = SelectField("Role", choices=[("Employee","Employee"), ("Manager","Manager"), ("Admin","Admin")])
    submit = SubmitField("Update User")