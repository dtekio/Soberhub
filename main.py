import os
from datetime import date
from functools import wraps

import bleach
from flask import Flask, abort, flash, redirect, render_template, url_for
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor
from flask_gravatar import Gravatar
from flask_login import (LoginManager, UserMixin, current_user, login_user,
                         logout_user)
from flask_sqlalchemy import SQLAlchemy
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from sqlalchemy.orm import relationship
from werkzeug.security import check_password_hash, generate_password_hash

from forms import (CommentForm, ContactForm, CreatePostForm, LoginForm,
                   RegisterForm, EventForm)

app = Flask(__name__)
app.secret_key = 'test'
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DATABASE_URL", "sqlite:///blog.db").replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)

gravatar = Gravatar(app,
                    size=100,
                    rating='g',
                    default='retro',
                    force_default=False,
                    force_lower=False,
                    use_ssl=False,
                    base_url=None)


def strip_invalid_html(content):
    allowed_tags = ['a', 'abbr', 'acronym', 'address', 'b', 'br', 'div', 'dl', 'dt',
                    'em', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hr', 'i', 'img',
                    'li', 'ol', 'p', 'pre', 'q', 's', 'small', 'strike',
                    'span', 'sub', 'sup', 'table', 'tbody', 'td', 'tfoot', 'th',
                    'thead', 'tr', 'tt', 'u', 'ul']

    allowed_attrs = {
        'a': ['href', 'target', 'title'],
        'img': ['src', 'alt', 'width', 'height'],
    }

    cleaned = bleach.clean(content,
                           tags=allowed_tags,
                           attributes=allowed_attrs,
                           strip=True)

    return cleaned


def admin_only(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if current_user.id != 1:
            return abort(403)
        return f(*args, **kwargs)
    return decorated_function


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))




class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True)
    password = db.Column(db.String(100))
    name = db.Column(db.String(100))
    posts = relationship("BlogPost", back_populates="author")
    comments = relationship("Comment", back_populates="comment_author")


class BlogPost(db.Model):  
    __tablename__ = "blog_posts"
    id = db.Column(db.Integer, primary_key=True)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    author = relationship("User", back_populates="posts")
    title = db.Column(db.String(250), unique=True, nullable=False)
    tag = db.Column(db.String(250), nullable=False)
    subtitle = db.Column(db.String(250), nullable=False)
    date = db.Column(db.String(250), nullable=False)
    body = db.Column(db.Text, nullable=False)
    img_url = db.Column(db.String(250), nullable=False)
    comments = relationship("Comment", back_populates="parent_post")


class Comment(db.Model):
    __tablename__ = "comments"
    id = db.Column(db.Integer, primary_key=True)
    text = db.Column(db.Text, nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    post_id = db.Column(db.Integer, db.ForeignKey("blog_posts.id"))
    comment_author = relationship("User", back_populates="comments")
    parent_post = relationship("BlogPost", back_populates="comments")
    
class Event(db.Model):
    __tablename__ = "events"
    id = db.Column(db.Integer, primary_key=True)
    calendar_id = db.Column(db.Integer)
    heading = db.Column(db.String(250), nullable=False)
    text = db.Column(db.Text, nullable=False)
    date = db.Column(db.Text, nullable=False)
db.create_all()


@app.route('/', methods=['POST', 'GET'])
def get_all_posts():
    fcalendar_events = db.session.query(Event).filter_by(calendar_id=1).all()[0:3]
    scalendar_events = db.session.query(Event).filter_by(calendar_id=2).all()[0:3]
    posts = BlogPost.query.all()
    lifestyle_posts = BlogPost.query.filter_by(tag="lifestyle")
    technologies_posts = BlogPost.query.filter_by(tag="technologies")
    waste_posts = BlogPost.query.filter_by(tag="waste")
    return render_template("index.html", fcalendar_events=fcalendar_events, scalendar_events=scalendar_events, all_posts=posts, lifestyle_posts=list(lifestyle_posts),technologies_posts=list(technologies_posts),waste_posts=list(waste_posts))

@app.route('/contact', methods=['POST', 'GET'])
def contact():
    contact = ContactForm()
    if contact.validate_on_submit():
        message = Mail(
            from_email=os.getenv('EMAIL'),
            to_emails=os.getenv('EMAIL'),
            subject='New Message',
            html_content=f'Name: {contact.name.data} | Email: {contact.email.data} | Phone: {contact.phone_number.data} | Message: «{contact.message.data}»'
        )
        try:
            sg = SendGridAPIClient(os.getenv('API_KEY_ECOLIFESTYLE'))
            response = sg.send(message)
            print(response.status_code)
            print(response.body)
            print(response.headers)
        except Exception as e:
            print(e)
        return render_template("contact.html", msg_sent=True, form=contact)
    return render_template("contact.html", msg_sent=False, form=contact)
    

@app.route('/register', methods=["GET", "POST"])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        if User.query.filter_by(email=form.email.data).first():
            flash(
                "You have already registered with this email address, log in instead.")
            return redirect(url_for('login'))
        hash_and_salted_password = generate_password_hash(
            form.password.data,
            method='pbkdf2:sha256',
            salt_length=8
        )
        new_user = User(
            email=form.email.data,
            name=form.name.data,
            password=hash_and_salted_password,
        )
        db.session.add(new_user)
        db.session.commit()
        login_user(new_user)
        return redirect(url_for("get_all_posts"))
    return render_template("register.html", form=form)


@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        email = form.email.data
        password = form.password.data

        user = User.query.filter_by(email=email).first()
        if not user:
            flash('This email address does not exist, please try again.')
            return redirect(url_for('login'))
        elif not check_password_hash(user.password, password):
            flash('Invalid password, try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('get_all_posts'))
    return render_template("login.html", form=form)


@app.route("/post/<int:post_id>", methods=["GET", "POST"])
def show_post(post_id):
    requested_post = BlogPost.query.get(post_id)
    form = CommentForm()

    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('You need to log in or register to leave a comment.')
            return redirect(url_for('login'))
        new_comment = Comment(
            text=strip_invalid_html(form.comment.data),
            author_id=current_user.id,
            post_id=post_id
        )
        db.session.add(new_comment)
        db.session.commit()
        return redirect(url_for('show_post', post_id=post_id))
    return render_template("post.html", post=requested_post, form=form)


@app.route("/new-post", methods=["GET", "POST"])
@admin_only
def add_new_post():
    form = CreatePostForm()
    if form.validate_on_submit():
        new_post = BlogPost(
            title=form.title.data,
            subtitle=form.subtitle.data,
            body=strip_invalid_html(form.body.data),
            tag=form.tag.data,
            img_url=form.img_url.data,
            author=current_user,
            date=date.today().strftime("%B %d, %Y")
        )
        db.session.add(new_post)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)


@app.route("/edit-post/<int:post_id>", methods=["GET", "POST"])
@admin_only
def edit_post(post_id):
    post = BlogPost.query.get(post_id)
    edit_form = CreatePostForm(
        title=post.title,
        subtitle=post.subtitle,
        img_url=post.img_url,
        author=post.author,
        body=post.body
    )
    if edit_form.validate_on_submit():
        post.title = edit_form.title.data
        post.subtitle = edit_form.subtitle.data
        post.tag = edit_form.tag.data
        post.img_url = edit_form.img_url.data
        post.body = strip_invalid_html(edit_form.body.data)
        db.session.commit()
        return redirect(url_for("show_post", post_id=post.id))
    return render_template("make-post.html", form=edit_form, is_edit=True)


@app.route("/delete/<int:post_id>", methods=["GET", "POST"])
@admin_only
def delete_post(post_id):
    post_to_delete = BlogPost.query.get(post_id)
    db.session.delete(post_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@app.route("/calendar/<int:calendar_id>")
def calendar(calendar_id):
    all_events = db.session.query(Event).filter_by(calendar_id=calendar_id).all()
    return render_template("calendar.html", all_events=all_events) 

@app.route("/new-event", methods=["GET", "POST"])
@admin_only
def add_new_event():
    form = EventForm()
    if form.validate_on_submit():
        event = Event(
            calendar_id = form.calendar_id.data,
            heading = form.heading.data,
            date = form.date.data,
            text = form.text.data
        )
        db.session.add(event)
        db.session.commit()
        return redirect(url_for("get_all_posts"))
    return render_template("make-post.html", form=form)

@app.route("/event/<int:event_id>", methods=["GET", "POST"])
def show_event(event_id):
    requested_event = Event.query.get(event_id)
    return render_template("event.html", event=requested_event)

@app.route("/delete_event/<int:event_id>", methods=["GET", "POST"])
@admin_only
def delete_event(event_id):
    event_to_delete = Event.query.get(event_id)
    db.session.delete(event_to_delete)
    db.session.commit()
    return redirect(url_for('get_all_posts'))

@app.route("/calculator")
def calculator():
    return render_template("calculator.html")

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('get_all_posts'))

if __name__ == "__main__":
    app.run()
