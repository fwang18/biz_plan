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
    return render_template('index.html')


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
    return render_template('upload.html', filenames=sorted_files)


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """
    This route is expecting a parameter containing the name
    of a file. Then it will locate that file on the upload
    directory and show it on the browser, so if the user uploads
    an image, that image is going to be show after the upload
    """
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=int("80"),
        debug=True
        )
