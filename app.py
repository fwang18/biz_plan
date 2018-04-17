import os
import random

# We'll render HTML templates and access data sent by POST
# using the request object from flask. Redirect and url_for
# will be used to redirect the user once the upload is done
# and send_from_directory will help us to send/show on the
# browser the file that the user just uploaded
from flask import Flask, render_template, request, \
    redirect, url_for, send_from_directory
from werkzeug import secure_filename


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
    return render_template('dashboard_upload.html', name=current_user.username)


@app.route('/upload', methods=['POST'])
def upload():
    """
    This route will process the file upload
    """
    # Get the name of the uploaded files
    uploaded_files = request.files.getlist("file[]")
    filenames = []
    for file in uploaded_files:
        # Check if the file is one of the allowed types/extensions
        if file and allowed_file(file.filename):
            # Make the filename safe, remove unsupported chars
            filename = secure_filename(file.filename)
            # Move the file form the temporal folder to the upload
            # folder we setup
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            # Save the filename into a list, we'll use it later
            filenames.append(filename)
            # Redirect the user to the uploaded_file route, which
            # will basically show on the browser the uploaded file
    # Show images in sorted order based on model results.
    # To be replaced with model results later!.
    sorted_files = random.sample(filenames, len(filenames))
    # Load an html page with a link to each uploaded file
    return render_template('dashboard_results.html', filenames=sorted_files, name=current_user.username)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    This route is expecting a parameter containing the name
    of a file. Then it will locate that file on the upload
    directory and show it on the browser, so if the user uploads
    an image, that image is going to be show after the upload
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)




###login start
from flask import Flask, render_template, redirect, url_for
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
from flask_sqlalchemy  import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user

# app.config['SECRET_KEY'] = 'Thisissupposedtobesecret!'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True


bootstrap = Bootstrap(app)
db = SQLAlchemy(app)
login_manager = LoginManager()
# login_manager.init_app(app)
login_manager.login_view = 'login'

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(15), unique=True)
    email = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(80))

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(), Length(min=4, max=15)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max=80)])


@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user is not None and check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            return redirect(url_for('index'))

        else:
            return render_template('login_error.html', form=form)

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    user_count = User.query.filter_by(username=form.username.data).count()
    if (user_count > 0):
        form = RegisterForm()
        return render_template('signup_error.html', form=form)

    elif form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)


@app.route('/dashboard')
@login_required
def dashboard():
    return render_template('dashboard_upload.html', name=current_user.username)

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('home.html')
###login end




if __name__ == "__main__":
    login_manager.init_app(app)
    app.secret_key = os.urandom(24)
    db.create_all()
    db.session.commit()
    app.run(host="0.0.0.0", port=8080, debug=True)
