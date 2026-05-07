"""
app/utils/forms.py — WTForms definitions
"""

from flask_wtf import FlaskForm
from wtforms import BooleanField, EmailField, PasswordField, SelectField, StringField, SubmitField
from wtforms.validators import DataRequired, Email, EqualTo, Length, Optional, Regexp


class LoginForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[DataRequired(), Length(3, 64)],
        render_kw={
            "autocomplete": "username",
            "aria-label": "Username",
            "aria-required": "true",
            "placeholder": "Enter your username",
        },
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(8, 128)],
        render_kw={
            "autocomplete": "current-password",
            "aria-label": "Password",
            "aria-required": "true",
            "placeholder": "Enter your password",
        },
    )
    remember_me = BooleanField(
        "Keep me signed in",
        render_kw={"aria-label": "Keep me signed in"},
    )
    submit = SubmitField("Sign In")


class AddUserForm(FlaskForm):
    username = StringField(
        "Username",
        validators=[
            DataRequired(),
            Length(3, 64),
            Regexp(r"^[\w.-]+$", message="Alphanumeric, dots, dashes only."),
        ],
        render_kw={"aria-label": "Username", "aria-required": "true"},
    )
    email = EmailField(
        "Email address",
        validators=[DataRequired(), Email(), Length(max=120)],
        render_kw={"aria-label": "Email address", "aria-required": "true"},
    )
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(10, 128)],
        render_kw={"aria-label": "Password", "aria-required": "true"},
    )
    confirm = PasswordField(
        "Confirm password",
        validators=[DataRequired(), EqualTo("password", message="Passwords must match.")],
        render_kw={"aria-label": "Confirm password", "aria-required": "true"},
    )
    role = SelectField(
        "Role",
        choices=[("viewer", "Viewer"), ("operator", "Operator"), ("admin", "Administrator")],
        validators=[DataRequired()],
        render_kw={"aria-label": "User role", "aria-required": "true"},
    )
    submit = SubmitField("Add User")


class AllowIPForm(FlaskForm):
    ip_address = StringField(
        "IP Address / CIDR",
        validators=[DataRequired(), Length(max=50)],
        render_kw={
            "aria-label": "IP Address or CIDR range",
            "aria-required": "true",
            "placeholder": "e.g. 192.168.1.100 or 10.0.0.0/24",
        },
    )
    label = StringField(
        "Label (optional)",
        validators=[Optional(), Length(max=80)],
        render_kw={"aria-label": "Friendly label for this IP", "placeholder": "e.g. Office WiFi"},
    )
    submit = SubmitField("Add to Allow-list")
