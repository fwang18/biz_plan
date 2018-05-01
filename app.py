"""
@author: Chen Wang, Fei Liu
"""

import os
import numpy as np

# We'll render HTML templates and access data sent by POST
# using the request object from flask. Redirect and url_for
# will be used to redirect the user once the upload is done
# and send_from_directory will help us to send/show on the
# browser the file that the user just uploaded
from flask import Flask, render_template, request, \
    redirect, url_for, send_from_directory
from werkzeug import secure_filename
from flask import Flask, render_template, redirect, url_for, session
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, \
    check_password_hash
from flask_login import LoginManager, UserMixin, login_user,\
    login_required, logout_user, current_user
from predict import ImagePredictor
import datetime
from datetime import timedelta


app = Flask(__name__)


@app.route("/")
def home():
    """
    This function is to render home page HTML
    """
    return render_template('home.html')


@app.route("/contact")
def contact():
    """
    This function is to render CONTACT US HTML
    """
    return render_template('contact.html')


# This is the path to the upload directory
app.config['UPLOAD_FOLDER'] = 'uploads/'
# These are the extension that we are accepting to be uploaded
app.config['ALLOWED_EXTENSIONS'] = \
    set(['txt', 'pdf', 'png', 'jpg', 'jpeg', 'gif'])


def allowed_file(filename):
    """
    This function is to test whether a given file extension is valid.
    Return whether it's an allowed type or not.
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower()\
           in app.config['ALLOWED_EXTENSIONS']


@app.route('/index')
def index():
    """
    This route will show a form to perform an AJAX request
    jQuery is loaded to execute the request and update the
    value of the operation
    """
    # check user status
    # List of status objects for a user
    user_all_status = User.query.filter_by(username=current_user.username).first().status
    # List of log objects for a user
    user_all_log = User.query.filter_by(username=current_user.username).first().log
    # Evaluation time in 30 days
    count = len([(datetime.datetime.now() - log.log_ts) < datetime.timedelta(days=30)
                 for log in user_all_log])
    # For free users, check number of evaluation times.
    if len(user_all_status) == 0 and count == 5:
        messages = "You've reached 5 limit, please upgrade."
        session['messages'] = messages
        return redirect(url_for('upgrade'))
    else:
        return render_template('dashboard_upload.html', name=current_user.username)


# This is to create user database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.login_view = 'login'


# Create table User into database
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))
    # reference column for Payment class
    status = db.relationship('Payment', backref='users')
    # reference column for Logs class
    log = db.relationship('Logs', backref='users')


# Create user payment table into database
class Payment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    status = db.Column(db.String(2))
    pay_time = db.Column(db.DateTime)


# Create user logs table into database
class Logs(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    person_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    log_ts = db.Column(db.DateTime)
    num_pic = db.Column(db.Integer)


@login_manager.user_loader
def load_user(user_id):
    """
    This function is to load user from database before
    every request.
    """
    return User.query.get(int(user_id))


# Create login form.
class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired()])
    password = PasswordField('password', validators=[InputRequired()])
    remember = BooleanField('remember me')


# Create sign up form.
class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(),
                                             Email(message='Invalid email'),
                                             Length(max=50)])
    username = StringField('username', validators=[
        InputRequired(message='Username Required'),
        Length(min=4, max=15)])
    password = PasswordField('password', validators=[
        InputRequired(message='Password Required'),
        Length(min=8, max=80)])


@app.route('/login', methods=['GET', 'POST'])
def login():
    """
    This route is for users to login.
    """
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        # Allow registered users with correct
        # password to go to upload images page.
        if user is not None and \
                check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            session['logged_in'] = True
            return redirect(url_for('index'))
        # Throw error if user hasn't signed up or input wrong password.
        else:
            return render_template('login.html',
                                   form=form,
                                   message="Invalid Username or Password")

    return render_template('login.html', form=form)


@app.route('/signup', methods=['GET', 'POST'])
def signup():
    """
    This route is for users to sign up new account
    and redirect them to login page once done.
    """
    form = RegisterForm()
    user_count = User.query.filter_by(username=form.username.data).count()
    # Throw warning message for existing users.
    if user_count > 0:
        form = RegisterForm()
        return render_template('signup.html',
                               form=form,
                               message="Username Already Exist")
    # Create sign up form for uses to fill.
    elif form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data,
                                                 method='sha256')
        new_user = User(username=form.username.data,
                        email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('signup_landing')) ###test

    return render_template('signup.html', form=form)


@app.route('/signup_landing')
def signup_landing():
    return render_template('signup_landing.html')


@app.route('/upgrade_landing')
def upgrade_landing():
    return render_template('upgrade_landing.html')


@app.route('/upload', methods=['POST'])
def upload():
    """
    This route will process the file upload
    """
    # Get the name of the uploaded files
    uploaded_files = request.files.getlist("file[]")
    filenames = []
    if len(uploaded_files) > 5:
        return render_template('dashboard_upload.html',
                               name=current_user.username, error=1)

    for file in uploaded_files:
        # Check if the file is one of the allowed types/extensions
        if file and allowed_file(file.filename):
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file.filename)
            # Move the file form the temporal folder to the upload
            # folder we setup
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Save the filename into a list, we'll use it later
            filenames.append(os.path.join(app.config['UPLOAD_FOLDER'],
                                          filename))
        # Throw an error for images with improper extension.
        if allowed_file(file.filename) is False:
                return render_template('dashboard_upload.html',
                                       name=current_user.username,
                                       error=2, wrongfile=file.filename)
    # Redirect the user to the uploaded_file route, which
    # will basically show on the browser the uploaded file
    # Show images in sorted order based on model results.
    m = ImagePredictor('model/cnn_model.pt')
    sorted_files = list(np.array(filenames)[m.rank(filenames)])
    files = [f.split('/')[1] for f in sorted_files]
    # Record users evaluation time in Logs table

    user_s = User.query.filter_by(username=current_user.username).first()
    if len(user_s.status) == 0:
        user_log = Logs(log_ts=datetime.datetime.now(), num_pic=len(files), users=user_s)
        db.session.add(user_log)
        db.session.commit()

    # Load an html page with a link to each uploaded file
    return render_template('dashboard_results.html',
                           filenames=sorted_files,
                           name=current_user.username, files=files)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    This route is expecting a parameter containing the name
    of a file. Then it will locate that file on the upload
    directory and show it on the browser, so if the user uploads
    an image, that image is going to be show after the upload
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


# Create user payment form.
class PaymentForm(FlaskForm):
    name = StringField('Name', validators=[InputRequired()])
    credit_num = StringField('Credit card number',
                             validators=[InputRequired()])
    exp_date = StringField('Expiration date',
                           validators=[InputRequired()])
    sec_code = StringField('Security code',
                           validators=[InputRequired()])


@app.route("/upgrade", methods=['GET', 'POST'])
def upgrade():
    """
    This function is to render Upgrade HTML
    Allowing user to provide payment info
    """
    form = PaymentForm()

    if form.validate_on_submit():

        user_s = User.query.filter_by(username=current_user.username).first()
        user_pay = Payment(status=1, pay_time=datetime.datetime.now(), users=user_s)
        db.session.add(user_pay)
        db.session.commit()
        return redirect(url_for('upgrade_landing'))

    # check user status
    # List of status objects for a user
    user_all_status = User.query.filter_by(username=current_user.username).first().status
    # List of log objects for a user
    user_all_log = User.query.filter_by(username=current_user.username).first().log
    # Evaluation time in 30 days
    count = len([(datetime.datetime.now() - log.log_ts) < datetime.timedelta(days=30)
                 for log in user_all_log])
    # For free users, check number of evaluation times.
    if len(user_all_status) == 0 and count == 5:
        return render_template('upgrade.html', form=form, error=1)
    else:
        return render_template('upgrade.html', form=form)


@app.route("/profile")
def profile():
    """
    This function is to render User Profile HTML
    """
    # check user status
    user_all_status = User.query.filter_by(username=current_user.username).first().status
    # Free user
    if len(user_all_status) == 0:
        recent_status = 0
        user_all_log = User.query.filter_by(username=current_user.username).first().log
        # Evaluation time in 30 days
        count = len([(datetime.datetime.now() - log.log_ts) < datetime.timedelta(days=30)
                     for log in user_all_log])
        free = 5-count
        exp_date = -1
    # Paid user
    else:
        recent_status = int(user_all_status[-1].status)
        exp_date = (user_all_status[-1].pay_time + datetime.timedelta(days=30)).date()
        free = -1

    return render_template('user_profile.html', name=current_user.username,
                           email=current_user.email, plan=recent_status,
                           plan_date=exp_date, free=free)


@app.route('/logout')
@login_required
def logout():
    """
    This route is to let users logout and redirect them
    to HOME page.
    """
    logout_user()
    session['logged_in'] = False
    return render_template('home.html')


if __name__ == "__main__":
    login_manager.init_app(app)
    app.secret_key = os.urandom(24)
    db.create_all()
    db.session.commit()
    app.run(host="0.0.0.0", port=8080, debug=True)