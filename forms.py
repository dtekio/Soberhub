from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired, Email

class ContactForm(FlaskForm):
    name = StringField("Имя", validators=[DataRequired()])
    email = StringField("Электронная почта", validators=[DataRequired(), Email()])
    phone_number = StringField("Телефонный номер", validators=[DataRequired()])
    submit = SubmitField("Отправить")