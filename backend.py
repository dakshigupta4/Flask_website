from flask import Flask, request, jsonify
import sqlite3
import os
from datetime import datetime
import csv

app = Flask(__name__)

# Function to initialize the database
def init_db():
    if not os.path.exists('contact_form.db'):  # Only initialize if the file does not exist
        conn = sqlite3.connect('contact_form.db')
        cursor = conn.cursor()
        
        # Create the table with the updated schema
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT NOT NULL,
                message TEXT NOT NULL,
                service TEXT,
                phone_number TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()
        conn.close()

# Function to save form submissions to a CSV file
def save_to_csv(data):
    file_exists = os.path.isfile('submissions.csv')
    with open('submissions.csv', mode='a', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        if not file_exists:
            # Write the header only once
            writer.writerow(['Name', 'Email', 'Message', 'Service', 'Phone Number', 'Timestamp'])
        writer.writerow([data['name'], data['email'], data['message'], data['service'], data['phone_number'], data['timestamp']])

# Function to save form submissions to a log file
def save_to_log(data):
    with open('submissions.log', mode='a', encoding='utf-8') as file:
        file.write(f"Name: {data['name']}, Email: {data['email']}, Message: {data['message']}, "
                   f"Service: {data['service']}, Phone: {data['phone_number']}, Timestamp: {data['timestamp']}\n")

# Function to check if email and phone number exist in the database
def check_user_credentials(email, phone_number):
    conn = sqlite3.connect('contact_form.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM submissions WHERE email = ? AND phone_number = ?
    ''', (email, phone_number))
    
    user = cursor.fetchone()  # Get the first matching user (if any)
    conn.close()
    
    return user is not None  # If user is found, return True; otherwise, False

# Route to handle form submission
@app.route('/submit-form', methods=['POST'])
def submit_form():
    # Extract form data
    client_name = request.form.get('Client-Name')
    client_email = request.form.get('Client-Email')
    message = request.form.get('Client-s-Message')
    service = request.form.get('services')
    phone_number = request.form.get('field-5')

    # Check if the email and phone number are valid (i.e., exist in the database)
    if not check_user_credentials(client_email, phone_number):
        return jsonify({"status": "error", "message": "Invalid email or phone number"})

    # Check if any critical field is missing
    if not client_name or not client_email or not message:
        return jsonify({"status": "error", "message": "Name, email, and message are required."})

    # Save to the database
    conn = sqlite3.connect('contact_form.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO submissions (name, email, message, service, phone_number, timestamp)
        VALUES (?, ?, ?, ?, ?, ?)
    ''', (client_name, client_email, message, service, phone_number, datetime.now()))
    conn.commit()
    conn.close()

    # Save to CSV
    save_to_csv({
        'name': client_name,
        'email': client_email,
        'message': message,
        'service': service,
        'phone_number': phone_number,
        'timestamp': datetime.now()
    })

    # Save to log file
    save_to_log({
        'name': client_name,
        'email': client_email,
        'message': message,
        'service': service,
        'phone_number': phone_number,
        'timestamp': datetime.now()
    })

    return jsonify({"status": "success", "message": "Form submitted successfully"})

# Route to handle user login
@app.route('/login', methods=['POST'])
def login():
    # Get the login credentials (email and phone number)
    email = request.json.get('email')
    phone_number = request.json.get('phone_number')

    # Check if user exists with the given email and phone number
    user_exists = check_user_credentials(email, phone_number)
    
    if user_exists:
        return jsonify({"status": "success", "message": "Login successful"})
    else:
        return jsonify({"status": "error", "message": "Invalid email or phone number"})

# Start the Flask app
if __name__ == '__main__':
    init_db()  # Initialize the database
    app.run(debug=True)  # Run the Flask server
