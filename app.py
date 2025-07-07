from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
import mysql.connector
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

# ---------------------------
# CONFIGURATION
# ---------------------------
USERNAME = "Pixadmin"
PASSWORD = "Pixd.t"
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

DB_CONFIG = {
    "host": os.getenv("DB_HOST"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "database": os.getenv("DB_NAME")
}

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------------------
# UTILITIES
# ---------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

def get_db_connection():
    return mysql.connector.connect(**DB_CONFIG)

# ---------------------------
# STATIC FILE SERVE
# ---------------------------
@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_from_directory(app.config["UPLOAD_FOLDER"], filename)

# ---------------------------
# IMAGE UPLOAD ROUTE
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
        full_url = f"https://pixdotbackend.onrender.com/uploads/{unique_filename}"
        return jsonify({"imageUrl": full_url}), 200

    return jsonify({"error": "Invalid file type"}), 400

# ---------------------------
# CONTACT EMAIL ROUTE
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
    We'll get back to you shortly.

    📞 +91-87789 96278, 87789 64644
    🌐 www.pixdotsolutions.com
    """

    try:
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(GMAIL_USER, GMAIL_PASSWORD)

        admin_msg = MIMEMultipart()
        admin_msg["From"] = GMAIL_USER
        admin_msg["To"] = GMAIL_USER
        admin_msg["Subject"] = admin_subject
        admin_msg.attach(MIMEText(admin_body, "plain"))
        server.send_message(admin_msg)

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
# ADMIN LOGIN
# ---------------------------
@app.route("/api/login", methods=["POST"])
def login():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if username == USERNAME and password == PASSWORD:
        return jsonify({"success": True}), 200
    return jsonify({"success": False, "message": "Invalid credentials"}), 401

# ---------------------------
# CASE STUDY ROUTES (MySQL)
# ---------------------------
@app.route("/api/case-studies", methods=["GET"])
def get_case_studies():
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM case_studies")
        rows = cursor.fetchall()
        db.close()
        return jsonify(rows)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/case-studies/<int:case_id>", methods=["GET"])
def get_case_study(case_id):
    try:
        db = get_db_connection()
        cursor = db.cursor(dictionary=True)
        cursor.execute("SELECT * FROM case_studies WHERE id = %s", (case_id,))
        result = cursor.fetchone()
        db.close()

        if not result:
            return jsonify({"error": "Not found"}), 404

        # Convert side_images and content from JSON string to Python array
        result["sideImages"] = json.loads(result["side_images"]) if result["side_images"] else []
        result["content"] = json.loads(result["content"]) if result["content"] else []

        # Optional: remove original snake_case fields
        del result["side_images"]
        del result["content"]  # remove this if you renamed instead of added

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/add-case-study", methods=["POST"])
def add_case_study():
    try:
        data = request.get_json()
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            INSERT INTO case_studies
            (title, client, date, duration, industry, category, image, side_images, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["title"], data["client"], data["date"], data["duration"],
            data["industry"], data["category"], data["image"],
            json.dumps(data["side_images"]), json.dumps(data["content"])
        ))
        db.commit()
        db.close()
        return jsonify({"success": True, "message": "Case study added"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/update-case-study/<int:case_id>", methods=["PUT"])
def update_case_study(case_id):
    try:
        data = request.get_json()
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("""
            UPDATE case_studies SET
            title=%s, client=%s, date=%s, duration=%s,
            industry=%s, category=%s, image=%s,
            side_images=%s, content=%s
            WHERE id=%s
        """, (
            data["title"], data["client"], data["date"], data["duration"],
            data["industry"], data["category"], data["image"],
            json.dumps(data["side_images"]), json.dumps(data["content"]), case_id
        ))
        db.commit()
        db.close()
        return jsonify({"success": True, "message": "Updated"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/delete-case-study/<int:case_id>", methods=["DELETE"])
def delete_case_study(case_id):
    try:
        db = get_db_connection()
        cursor = db.cursor()
        cursor.execute("DELETE FROM case_studies WHERE id = %s", (case_id,))
        db.commit()
        db.close()
        return jsonify({"success": True, "message": "Deleted"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------
# MAIN ENTRY
# ---------------------------
if __name__ == "__main__":
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.run(debug=True)


