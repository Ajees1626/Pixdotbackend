from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ---------------------------
# CONFIGURATION
# ---------------------------
USERNAME = "Pixadmin"
PASSWORD = "Pixd.t"
DATA_FILE = "CasestudyDetails.json"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------------------
# UTILITIES
# ---------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------
# STATIC FILE SERVE
# ---------------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ---------------------------
# ✅ FIXED IMAGE UPLOAD ROUTE (supports image + file)
# ---------------------------
@app.route("/api/upload-image", methods=["POST"])
def upload_image():
    file = request.files.get("image") or request.files.get("file")

    if not file or file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        unique_filename = f"{int(float(os.times()[4]*1000))}_{filename}"
        save_path = os.path.join(app.config["UPLOAD_FOLDER"], unique_filename)
        file.save(save_path)

        return jsonify({"imageUrl": f"/uploads/{unique_filename}"}), 200
    else:
        return jsonify({"error": "Invalid file type"}), 400

# ---------------------------
# CONTACT FORM EMAIL ROUTE
# ---------------------------
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

    user_subject = "Thank You for Contacting Pixdot!"
    user_body = f"""
    Hi {first_name},

    Thank you for reaching out to Pixdot!

    We’ve received your message, and our team will get back to you shortly.

    📞 Need urgent help? Call us at +91-87789 96278, 87789 64644
    🌐 Website: www.pixdotsolutions.com

    - Team Pixdot
    """

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)

        # Admin email
        admin_msg = MIMEMultipart()
        admin_msg["From"] = GMAIL_USER
        admin_msg["To"] = GMAIL_USER
        admin_msg["Subject"] = admin_subject
        admin_msg.attach(MIMEText(admin_body, "plain"))
        server.send_message(admin_msg)

        # User reply
        user_msg = MIMEMultipart()
        user_msg["From"] = GMAIL_USER
        user_msg["To"] = email
        user_msg["Subject"] = user_subject
        user_msg.attach(MIMEText(user_body, "plain"))
        server.send_message(user_msg)

        server.quit()
        return jsonify({"message": "Message sent successfully via email!"}), 200

    except Exception as e:
        print("Email error:", str(e))
        return jsonify({"error": "Failed to send email."}), 500

# ---------------------------
# ADMIN LOGIN ROUTE
# ---------------------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username == USERNAME and password == PASSWORD:
        return jsonify({"success": True}), 200
    else:
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

# ---------------------------
# CASE STUDY ROUTES
# ---------------------------
@app.route("/api/case-studies", methods=["GET"])
def get_case_studies():
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            data = []
        return jsonify(data)
    except Exception as e:
        print("Error reading case studies:", e)
        return jsonify({"error": "Failed to read case studies"}), 500

@app.route("/api/case-studies/<int:case_id>", methods=["GET"])
def get_case_study(case_id):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        case_study = next((item for item in data if item["id"] == case_id), None)
        if not case_study:
            return jsonify({"error": "Not found"}), 404
        return jsonify(case_study)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/add-case-study", methods=["POST"])
def add_case_study():
    try:
        data = request.get_json()
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                existing = json.load(f)
        else:
            existing = []

        data["id"] = max([item["id"] for item in existing], default=0) + 1
        existing.append(data)

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(existing, f, indent=2)

        return jsonify({"success": True, "message": "Case study added"}), 201

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/update-case-study/<int:case_id>", methods=["PUT"])
def update_case_study(case_id):
    try:
        data = request.get_json()
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            studies = json.load(f)

        updated = False
        for i, study in enumerate(studies):
            if study["id"] == case_id:
                studies[i] = {**study, **data, "id": case_id}
                updated = True
                break

        if not updated:
            return jsonify({"success": False, "message": "Not found"}), 404

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(studies, f, indent=2)

        return jsonify({"success": True, "message": "Updated"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/delete-case-study/<int:case_id>", methods=["DELETE"])
def delete_case_study(case_id):
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        updated = [item for item in data if item["id"] != case_id]

        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(updated, f, indent=2)

        return jsonify({"success": True, "message": "Deleted"}), 200

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------
# MAIN ENTRY POINT
# ---------------------------
if __name__ == "__main__":
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.run(debug=True)



