import requests
from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file, jsonify
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

                    return jsonify({"download_url": url_for('download_file', filename=output_filename, _external=True)})
                else:
                    return jsonify({"error": "Processing failed"}), 500
            except Exception as e:
                return jsonify({"error": str(e)}), 500
        else:
            return jsonify({"error": "Invalid file type"}), 400

    return render_template('upload.html')

@app.route('/download/<filename>')
def download_file(filename):
    return send_file(filename, as_attachment=True)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)