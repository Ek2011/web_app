from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from flask_wtf.file import FileField
from wtforms.validators import DataRequired


class CommForm(FlaskForm):
    content = TextAreaField("Содержание")
    submit = SubmitField('Применить')
