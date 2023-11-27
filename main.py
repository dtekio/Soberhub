import os

import bleach
from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_ckeditor import CKEditor

from flask_sqlalchemy import SQLAlchemy
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail

from forms import ContactForm

app = Flask(__name__)
app.secret_key = 'test'
ckeditor = CKEditor(app)
Bootstrap(app)

app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    "DATABASE_URL", "sqlite:///blog.db").replace('postgres://', 'postgresql://')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

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
        return render_template("index.html", msg_sent=True, form=contact)
    return render_template("index.html", msg_sent=False, form=contact)

if __name__ == "__main__":
    app.run(debug=True)
