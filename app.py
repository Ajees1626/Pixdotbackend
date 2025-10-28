from flask import Flask, request, jsonify
from flask_cors import CORS
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

app = Flask(__name__)
CORS(app)

# Get environment variables
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
TO_EMAIL = os.getenv("TO_EMAIL")

@app.route('/', methods=['GET'])
def home():
    return "✅ Backend is running successfully!", 200


@app.route('/api/contact', methods=['POST'])
def contact_form():
    try:
        data = request.get_json()

        # Validate required fields
        required_fields = ["firstName", "lastName", "email", "subject", "message"]
        if not all(field in data and data[field] for field in required_fields):
            return jsonify({"error": "Required fields are missing."}), 400

        first_name = data.get("firstName")
        last_name = data.get("lastName")
        email = data.get("email")
        company = data.get("company", "Not provided")
        phone = data.get("phone", "Not provided")
        subject = data.get("subject")
        message = data.get("message")

        # Build the email
        msg = MIMEMultipart()
        msg["From"] = EMAIL_USER
        msg["To"] = TO_EMAIL
        msg["Subject"] = f"📩 New Contact Form Message: {subject}"

        body = f"""
        <h3>New Contact Form Submission</h3>
        <p><strong>First Name:</strong> {first_name}</p>
        <p><strong>Last Name:</strong> {last_name}</p>
        <p><strong>Email:</strong> {email}</p>
        <p><strong>Company:</strong> {company}</p>
        <p><strong>Phone:</strong> {phone}</p>
        <p><strong>Subject:</strong> {subject}</p>
        <p><strong>Message:</strong></p>
        <p>{message}</p>
        """

        msg.attach(MIMEText(body, "html"))

        # Send the email using Gmail SMTP
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASS)
            server.send_message(msg)

        return jsonify({"success": True, "message": "Email sent successfully!"}), 200

    except Exception as e:
        print("Error:", str(e))
        return jsonify({"error": "Failed to send email. Please try again later."}), 500


if __name__ == '__main__':
    # Render requires 0.0.0.0 host
    app.run(host="0.0.0.0", port=5000, debug=True)
