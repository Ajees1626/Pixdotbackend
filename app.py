from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

USERNAME = "Pixadmin"
PASSWORD = "Pixd.t"
GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")
JSON_FILE = "case_studies.json"

# Utility
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# Upload image
@app.route("/api/upload-image", methods=["POST"])
def upload_image():
    file = request.files.get("image") or request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if allowed_file(file.filename):
        filename = secure_filename(file.filename)
        path = os.path.join(app.config["UPLOAD_FOLDER"], filename)
        file.save(path)
        url = f"https://pixdotbackend.onrender.com/uploads/{filename}"
        return jsonify({"imageUrl": url})
    return jsonify({"error": "Invalid file type"}), 400

@app.route("/uploads/<filename>")
def serve_uploaded(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# Admin Login
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    if data.get("username") == USERNAME and data.get("password") == PASSWORD:
        return jsonify({"success": True})
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

# Send Email
@app.route("/api/contact", methods=["POST"])
def contact():
    data = request.json
    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)

        # Format for Admin
        admin_message = f"""
You have received a new contact message:

Name: {data.get('firstName', '')} {data.get('lastName', '')}
Email: {data.get('email', '')}
Phone: {data.get('phone', '')}
Company: {data.get('company', '')}
Subject: {data.get('subject', '')}
Message: {data.get('message', '')}

--
Thank you for reaching out to us.
Pixdot Solutions
"""

        # Format for User
        user_message = f"""
Dear {data.get('firstName', '')} {data.get('lastName', '')},

Thank you for submitting your message. Our team at Pixdot Solutions will contact you shortly.

Here is a copy of your message:

Subject: {data.get('subject', '')}
Message: {data.get('message', '')}

--
Pixdot Solutions Team
"""

        # Send to Admin
        admin_msg = MIMEMultipart()
        admin_msg["From"] = GMAIL_USER
        admin_msg["To"] = GMAIL_USER
        admin_msg["Subject"] = f"New Contact - {data.get('subject', '')}"
        admin_msg.attach(MIMEText(admin_message.strip(), "plain"))
        server.send_message(admin_msg)

        # Send to User
      # Send to User
        user_message = f"""
        Dear {data.get('firstName', '')},

    Thank you for reaching out to Pixdot!

    We’ve received your message, and our team will get back to you shortly. We appreciate your interest and look forward to connecting with you soon.

    📞 Need urgent help? Call us at +91-87789 96278, 87789 64644

    Meanwhile, feel free to explore our recent work: 
    🌐 Website: www.pixdotsolutins.com 

    Have a great day! 
    - Team Pixdot
        """

        user_msg = MIMEMultipart()
        user_msg["From"] = GMAIL_USER
        user_msg["To"] = data.get("email")
        user_msg["Subject"] = "Thank you for contacting Pixdot Solutions"
        user_msg.attach(MIMEText(user_message.strip(), "plain"))
        server.send_message(user_msg)


        server.quit()
        return jsonify({"message": "Message sent"}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# Case Study: GET All
@app.route("/api/case-studies", methods=["GET"])
def get_all():
    try:
        with open(JSON_FILE) as f:
            return jsonify(json.load(f))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Case Study: GET by ID
@app.route("/api/case-studies/<int:case_id>", methods=["GET"])
def get_one(case_id):
    try:
        with open(JSON_FILE) as f:
            data = json.load(f)
        case = next((item for item in data if item["id"] == case_id), None)
        return jsonify(case if case else {"error": "Not found"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Case Study: ADD
@app.route("/api/add-case-study", methods=["POST"])
def add_case():
    try:
        with open(JSON_FILE) as f:
            data = json.load(f)
        new_data = request.get_json()
        new_data["id"] = max([x["id"] for x in data], default=0) + 1
        data.append(new_data)
        with open(JSON_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Case Study: UPDATE
@app.route("/api/update-case-study/<int:case_id>", methods=["PUT"])
def update_case(case_id):
    try:
        updated = request.get_json()
        with open(JSON_FILE) as f:
            data = json.load(f)
        for i, case in enumerate(data):
            if case["id"] == case_id:
                data[i] = {**case, **updated, "id": case_id}
                break
        else:
            return jsonify({"error": "Not found"}), 404
        with open(JSON_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# Case Study: DELETE
@app.route("/api/delete-case-study/<int:case_id>", methods=["DELETE"])
def delete_case(case_id):
    try:
        with open(JSON_FILE) as f:
            data = json.load(f)
        data = [x for x in data if x["id"] != case_id]
        with open(JSON_FILE, "w") as f:
            json.dump(data, f, indent=2)
        return jsonify({"success": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    if not os.path.exists(JSON_FILE):
        with open(JSON_FILE, "w") as f:
            json.dump([], f)
    app.run(debug=True)

