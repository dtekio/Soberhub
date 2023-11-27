from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, SelectField, DateField
from wtforms.validators import DataRequired, URL, Email
from flask_ckeditor import CKEditorField


class CreatePostForm(FlaskForm):
    title = StringField("Название", validators=[DataRequired()])
    subtitle = StringField("Подназвание", validators=[DataRequired()])
    img_url = StringField("Ссылка на изображение", validators=[DataRequired(), URL()])
    tag = SelectField('Раздел', choices=[('lifestyle', 'Экологический образ жизни'), ('technologies', 'Экологические технологии'), ('waste', 'Переработка отходов')])
    body = CKEditorField("Содержание", validators=[DataRequired()])
    submit = SubmitField("Сохранить")


class RegisterForm(FlaskForm):
    email = StringField("Электронная почта", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    name = StringField("Никнейм", validators=[DataRequired()])
    submit = SubmitField("Зарегистрироваться")


class LoginForm(FlaskForm):
    email = StringField("Электронная почта", validators=[DataRequired(), Email()])
    password = PasswordField("Пароль", validators=[DataRequired()])
    submit = SubmitField("Войти")


class CommentForm(FlaskForm):
    comment = CKEditorField('Комментарий', validators=[DataRequired()])
    submit = SubmitField("Отправить")


class ContactForm(FlaskForm):
    name = StringField("Имя", validators=[DataRequired()])
    email = StringField("Электронная почта", validators=[DataRequired(), Email()])
    phone_number = StringField("Телефонный номер", validators=[DataRequired()])
    message = StringField("Сообщение", validators=[DataRequired()])
    submit = SubmitField("Отправить")

class EventForm(FlaskForm):
    calendar_id = SelectField('Календарь', choices=[('1', 'Календарь мероприятий и событий'), ('2', 'Календарь устойчивых покупок')])
    date = DateField('Дата (дд.мм.гггг)', format='%d.%m.%Y', validators=[DataRequired()])
    heading = StringField("Название", validators=[DataRequired()])
    text = StringField("Содержание", validators=[DataRequired()])
    submit = SubmitField("Отправить")