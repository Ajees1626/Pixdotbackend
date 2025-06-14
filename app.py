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

    # Email to Admin
    admin_subject = f"New Contact Form Submission: {subject}"
    admin_body = f"""
    You have received a new message from the contact form:

    Name: {first_name} {last_name}
    Email: {email}
    Phone: {phone}
    Company: {company}
    Subject: {subject}

    Message:
    {message}
    """
# Email to User (Auto-reply)
    user_subject = "Thank You for Contacting Pixdot!"
    user_body = f"""
    Hi {first_name},

    Thank you for reaching out to Pixdot!

    We’ve received your message, and our team will get back to you shortly. We appreciate your interest and look forward to connecting with you soon.

    📞 Need urgent help? Call us at +91-87789 96278, 87789 64644

    Meanwhile, feel free to explore our recent work:  
    🌐 Website: www.pixdotsolutins.com  

    Have a great day!  
    - Team Pixdot
    """


    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)

        # Send to Admin
        admin_msg = MIMEMultipart()
        admin_msg['From'] = GMAIL_USER
        admin_msg['To'] = GMAIL_USER
        admin_msg['Subject'] = admin_subject
        admin_msg.attach(MIMEText(admin_body, 'plain'))
        server.send_message(admin_msg)

        # Send to User
        user_msg = MIMEMultipart()
        user_msg['From'] = GMAIL_USER
        user_msg['To'] = email
        user_msg['Subject'] = user_subject
        user_msg.attach(MIMEText(user_body, 'plain'))
        server.send_message(user_msg)

        server.quit()

        return jsonify({"message": "Message sent successfully via email!"}), 200

    except Exception as e:
        print("Error sending email:", str(e))
        return jsonify({"error": "Failed to send email."}), 500

if __name__ == "__main__":
    app.run(debug=True)


