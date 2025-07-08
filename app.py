from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from werkzeug.utils import secure_filename
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os
import json
from dotenv import load_dotenv
from db import get_connection  # 🔁 Use Neon connection from db.py
import cloudinary
import cloudinary.uploader

load_dotenv()

app = Flask(__name__)
CORS(app)

# ---------------------------
# CONFIGURATION
# ---------------------------
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("USERPASS")
UPLOAD_FOLDER = "uploads"
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}

GMAIL_USER = os.getenv("GMAIL_USER")
GMAIL_PASSWORD = os.getenv("GMAIL_PASSWORD")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# ---------------------------
# UTILITIES
# ---------------------------
def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS

# ---------------------------
# STATIC FILE SERVE
# ---------------------------
@app.route("/api/upload-image", methods=["POST"])
def upload_image():
    file = request.files.get("image") or request.files.get("file")
    if not file or file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    try:
        upload_result = cloudinary.uploader.upload(file)
        print("Upload Result:", upload_result)  # Debug log
        return jsonify({"imageUrl": upload_result["secure_url"]}), 200
    except Exception as e:
        print("Cloudinary Upload Error:", str(e))
        return jsonify({"error": "Cloudinary upload failed"}), 500

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
# ✅ ADMIN LOGIN (SAFELY HANDLED JSON)
# ---------------------------
@app.route("/api/login", methods=["POST"])
def login():
    try:
        data = request.get_json(force=True)
        if not data:
            return jsonify({"success": False, "message": "No data received"}), 400

        username = data.get("username")
        password = data.get("password")

        if username == USERNAME and password == PASSWORD:
            return jsonify({"success": True}), 200
        return jsonify({"success": False, "message": "Invalid credentials"}), 401

    except Exception as e:
        print("Login error:", str(e))
        return jsonify({"success": False, "message": "Server error"}), 500

# ---------------------------
# CASE STUDY ROUTES (Neon/PostgreSQL)
# ---------------------------
@app.route("/api/case-studies", methods=["GET"])
def get_case_studies():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM case_studies ORDER BY id DESC")
        rows = cur.fetchall()
        columns = [desc[0] for desc in cur.description]
        result = [dict(zip(columns, row)) for row in rows]
        cur.close()
        conn.close()
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/case-studies/<int:case_id>", methods=["GET"])
def get_case_study(case_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT * FROM case_studies WHERE id = %s", (case_id,))
        row = cur.fetchone()
        columns = [desc[0] for desc in cur.description]
        if not row:
            return jsonify({"error": "Not found"}), 404

        result = dict(zip(columns, row))
        result["sideImages"] = result.pop("side_images", [])
        result["content"] = result.get("content", [])

        cur.close()
        conn.close()
        return jsonify(result)

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/add-case-study", methods=["POST"])
def add_case_study():
    try:
        data = request.get_json()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO case_studies
            (title, client, date, duration, industry, category, image, side_images, content)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::jsonb)
        """, (
            data["title"], data["client"], data["date"], data["duration"],
            data["industry"], data["category"], data["image"],
            json.dumps(data["side_images"]), json.dumps(data["content"])
        ))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Case study added"}), 201
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/update-case-study/<int:case_id>", methods=["PUT"])
def update_case_study(case_id):
    try:
        data = request.get_json()
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            UPDATE case_studies SET
            title=%s, client=%s, date=%s, duration=%s,
            industry=%s, category=%s, image=%s,
            side_images=%s::jsonb, content=%s::jsonb
            WHERE id=%s
        """, (
            data["title"], data["client"], data["date"], data["duration"],
            data["industry"], data["category"], data["image"],
            json.dumps(data["side_images"]), json.dumps(data["content"]), case_id
        ))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Updated"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route("/api/delete-case-study/<int:case_id>", methods=["DELETE"])
def delete_case_study(case_id):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("DELETE FROM case_studies WHERE id = %s", (case_id,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"success": True, "message": "Deleted"}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ---------------------------
# TEST DB CONNECTION ROUTE
# ---------------------------
@app.route("/test-db")
def test_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT NOW()")
        result = cur.fetchone()
        cur.close()
        conn.close()
        return {"status": "success", "time": str(result[0])}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ---------------------------
# MAIN ENTRY
# ---------------------------
if __name__ == "__main__":
    if not os.path.exists("uploads"):
        os.makedirs("uploads")
    app.run(debug=True)
