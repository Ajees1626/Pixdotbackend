from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env

app = Flask(__name__)
CORS(app)

GMAIL_USER = os.getenv('GMAIL_USER')
GMAIL_PASSWORD = os.getenv('GMAIL_PASSWORD')

@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.json

    first_name = data.get("firstName")
    last_name = data.get("lastName")
    email = data.get("email")
    phone = data.get("phone")
    company = data.get("company")
    subject = data.get("subject")
    message = data.get("message")

    email_subject = f"New Contact Form Submission: {subject}"
    email_body = f"""
    You have received a new message from the contact form:

    Name: {first_name} {last_name}
    Email: {email}
    Phone: {phone}
    Company: {company}
    Subject: {subject}

    Message:
    {message}
    """

    try:
        msg = MIMEMultipart()
        msg['From'] = GMAIL_USER
        msg['To'] = GMAIL_USER
        msg['Subject'] = email_subject
        msg.attach(MIMEText(email_body, 'plain'))

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.send_message(msg)
        server.quit()

        return jsonify({"message": "Message sent successfully via email!"}), 200

    except Exception as e:
        print("Error sending email:", str(e))
        return jsonify({"error": "Failed to send email."}), 500

if __name__ == "__main__":
    app.run(debug=True)

