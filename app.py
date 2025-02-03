from flask import Flask, render_template, request, redirect, url_for, session, flash, send_file
import pandas as pd
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Dummy user credentials for demonstration
USER_CREDENTIALS = {
    'username': 'user',
    'password': 'password'
}

# Define allowed file extensions for Excel files
ALLOWED_EXTENSIONS = {'xlsx', 'xls'}

# Function to check if a file has an allowed extension
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Function to call your colleague's AI system (replace with actual API/function call)
def call_ai_system(data):
    """
    Simulates calling the AI system to group account numbers and photos.
    Replace this with the actual API call or function call to your colleague's system.
    """
    # Example: Simulate grouping by account number
    grouped_data = data.groupby('Account Number')['File Name'].apply(list).reset_index()
    return grouped_data

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
        # Check if a file was uploaded
        if 'file' not in request.files:
            flash('No file uploaded. Please select an Excel file.', 'error')
            return redirect(request.url)

        file = request.files['file']

        # Check if the file has a filename
        if file.filename == '':
            flash('No file selected. Please select an Excel file.', 'error')
            return redirect(request.url)

        # Check if the file has an allowed extension
        if file and allowed_file(file.filename):
            # Read the Excel file
            df = pd.read_excel(file)

            # Check if the required columns exist
            if 'Account Number' not in df.columns or 'File Name' not in df.columns:
                flash('The Excel file must contain "Account Number" and "File Name" columns.', 'error')
                return redirect(request.url)

            # Call the AI system to group the data
            grouped_data = call_ai_system(df)

            # Save the grouped data to a new Excel file
            output_filename = 'grouped_data.xlsx'
            grouped_data.to_excel(output_filename, index=False)

            # Send the new Excel file to the user for download
            return send_file(output_filename, as_attachment=True)
        else:
            flash('Invalid file type. Please upload an Excel file.', 'error')

    return render_template('upload.html')

@app.route('/success')
def success():
    if not session.get('logged_in'):
        return redirect(url_for('login'))
    return render_template('success.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)