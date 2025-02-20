from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
import requests
from datetime import datetime
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# FastAPI Backend URL
FASTAPI_URL = "http://10.2.125.37:8000/process"  # Replace with actual URL

# Dummy user credentials
USER_CREDENTIALS = {
    'username': 'user',
    'password': 'password'
}

# Allowed file extensions
ALLOWED_EXTENSIONS = {'xlsx', 'xls', 'csv'}

# List to store upload history
UPLOAD_HISTORY = []

# List to store chat feedback
CHAT_FEEDBACK = []

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
            session['username'] = username  # Store username in session
            session['profile_pic'] = url_for('static', filename='profile_pics/default.png')  # Default profile picture
            return redirect(url_for('upload'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    return render_template('login.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload():
    if not session.get('logged_in'):
        return jsonify({"error": "Unauthorized"}), 401

    if request.method == 'POST':
        if 'file' not in request.files:
            return jsonify({"error": "No file uploaded"}), 400

        file = request.files['file']
        if file.filename == '':
            return jsonify({"error": "No file selected"}), 400

        if file and allowed_file(file.filename):
            try:
                files = {'file': (file.filename, file, 'multipart/form-data')}
                response = requests.post(FASTAPI_URL, files=files)

                if response.status_code == 200:
                    output_filename = 'processed_data.csv'
                    with open(output_filename, 'wb') as f:
                        f.write(response.content)

                    # Add to upload history
                    upload_entry = {
                        'username': session.get('username', 'Unknown'),
                        'filename': file.filename,
                        'upload_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'status': 'Success',
                        'download_url': url_for('download_file', filename=output_filename, _external=True)
                    }
                    UPLOAD_HISTORY.append(upload_entry)

                    return jsonify({"download_url": upload_entry['download_url']})
                else:
                    # Add to upload history with failed status
                    upload_entry = {
                        'username': session.get('username', 'Unknown'),
                        'filename': file.filename,
                        'upload_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        'status': 'Failed',
                        'error': 'Processing failed'
                    }
                    UPLOAD_HISTORY.append(upload_entry)

                    return jsonify({"error": "Processing failed"}), 500
            except Exception as e:
                # Add to upload history with error status
                upload_entry = {
                    'username': session.get('username', 'Unknown'),
                    'filename': file.filename,
                    'upload_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    'status': 'Error',
                    'error': str(e)
                }
                UPLOAD_HISTORY.append(upload_entry)

                return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "Invalid file type"}), 400

    return render_template('upload.html')

@app.route('/upload-history')
def upload_history():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    return render_template('upload_history.html', history=UPLOAD_HISTORY)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
    if not session.get('logged_in'):
        return redirect(url_for('login'))

    if request.method == 'POST':
        feedback_text = request.form.get('feedback')
        username = session.get('username', 'Unknown')
        profile_pic = session.get('profile_pic', url_for('static', filename='profile_pics/default.png'))
        feedback_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if feedback_text:
            feedback_entry = {
                'username': username,
                'profile_pic': profile_pic,
                'feedback': feedback_text,
                'time': feedback_time
            }
            CHAT_FEEDBACK.append(feedback_entry)
            flash('Feedback sent!', 'success')
        else:
            flash('Feedback cannot be empty.', 'error')

    return render_template('feedback.html', chat_feedback=CHAT_FEEDBACK, session=session)

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    session.pop('profile_pic', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)