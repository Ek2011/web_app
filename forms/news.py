from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, BooleanField, SubmitField
from flask_wtf.file import FileField
from wtforms.validators import DataRequired


class NewsForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    file = FileField('Прикрепить документ')
    is_private = BooleanField("Личное")
    submit = SubmitField('Применить')
