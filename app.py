from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import os
import pandas as pd
import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Dummy user credentials for demonstration
USER_CREDENTIALS = {
    'username': 'user',
    'password': 'password'
}

# Define allowed file extensions
ALLOWED_EXTENSIONS = {'jpg', 'jpeg', 'png', 'gif'}

# File paths for storing uploads and history
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
HISTORY_FILE = os.path.join(os.getcwd(), 'upload_history.csv')

# Ensure the upload folder exists
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def home():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        if username == USER_CREDENTIALS['username'] and password == USER_CREDENTIALS['password']:
            session['logged_in'] = True
            return redirect(url_for('upload'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        if 'files' not in request.files:
            flash('No files uploaded. Please select a folder.', 'error')
            return redirect(request.url)

        files = request.files.getlist('files')
        if len(files) == 0:
            flash('No files selected. Please select a folder.', 'error')
            return redirect(request.url)

        # Collect information about the uploaded images
        image_data = []
        for file in files:
            if file.filename != '':
                if file.filename.lower() in ['desktop.ini', 'thumbs.db']:
                    continue  # Skip system files

                if allowed_file(file.filename):
                    filename = secure_filename(file.filename)
                    file_path = os.path.join(UPLOAD_FOLDER, filename)
                    file.save(file_path)

                    # Record file details
                    file_info = {
                        'Filename': filename,
                        'File Size (Bytes)': os.path.getsize(file_path),
                        'Upload Date': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'File Path': file_path
                    }
                    image_data.append(file_info)

        if image_data:
            # Convert to DataFrame and save history
            df = pd.DataFrame(image_data)
            excel_filename = 'image_data.xlsx'
            excel_path = os.path.join(UPLOAD_FOLDER, excel_filename)
            df.to_excel(excel_path, index=False)

            # Append to history
            save_upload_history(image_data)

            return send_file(excel_path, as_attachment=True)

    return render_template('upload.html')

def save_upload_history(image_data):
    """Save uploaded files information to a CSV for history tracking."""
    df = pd.DataFrame(image_data)

    # If history file exists, append new data
    if os.path.exists(HISTORY_FILE):
        existing_df = pd.read_csv(HISTORY_FILE)
        df = pd.concat([existing_df, df], ignore_index=True)

    df.to_csv(HISTORY_FILE, index=False)

@app.route('/history')
def history():
    """Display upload history."""
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if os.path.exists(HISTORY_FILE):
        history_df = pd.read_csv(HISTORY_FILE)
        history_records = history_df.to_dict(orient='records')  # Convert to list of dictionaries
    else:
        history_records = []

    return render_template('history.html', history=history_records)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)
