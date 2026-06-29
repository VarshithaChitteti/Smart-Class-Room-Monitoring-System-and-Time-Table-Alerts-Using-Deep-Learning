from flask import Flask, render_template, request, redirect, url_for, flash, jsonify, session
from werkzeug.utils import secure_filename
import json
import base64
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

# ==============================
# USERS (Role Based Access)
# ==============================
users = {
    "admin": {"password": "admin123", "role": "admin"},
    "Ms.Ch.Varshitha": {"password": "12345", "role": "faculty"},
    "Ms.M.DivyaSri": {"password": "12345", "role": "faculty"},
    "Ms.E.Tejaswani": {"password": "12345", "role": "faculty"},
    "Mrs.P.Madhavi": {"password": "12345", "role": "faculty"},
    "Mr.P.Muthyalu": {"password": "12345", "role": "faculty"},
    "Ms.P.Jasmine": {"password": "12345", "role": "faculty"}
}

STATUS_FILE = "status.json"
FACULTY_FILE = "faculty_data.json"
TIMETABLE_FILE = "timetable.json"
PHOTOS_FOLDER = "static/faculty_photos"

# ==============================
# Reset status when app starts
# ==============================
def reset_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            current = json.load(f)
    else:
        current = [
            {"room": "CSE-A", "status": "Absent", "faculty": ""},
            {"room": "CSE-B", "status": "Absent", "faculty": ""},
            {"room": "CSE-C", "status": "Absent", "faculty": ""}
        ]

    for room in current:
        room["status"] = "Absent"
        room["faculty"] = ""

    with open(STATUS_FILE, "w") as f:
        json.dump(current, f, indent=4)

reset_status()

# ==============================
# LOGIN
# ==============================
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username in users and users[username]["password"] == password:
            session["username"] = username
            session["role"] = users[username]["role"]

            # ✅ Role-based redirect
            if session["role"] == "admin":
                return redirect("/dashboard")
            else:
                return redirect("/faculty_report")

        else:
            flash("Invalid credentials!")

    return render_template("login.html")
# ==============================
# LOAD FUNCTIONS
# ==============================
def load_class_status():
    if os.path.exists(STATUS_FILE):
        with open(STATUS_FILE, "r") as f:
            return json.load(f)
    return []

def load_faculty_data():
    if os.path.exists(FACULTY_FILE):
        with open(FACULTY_FILE, "r") as f:
            return json.load(f)
    return {}

def enrich_class_status(classrooms, faculty_data):
    for room in classrooms:
        faculty_id = room.get("faculty", "")

        if faculty_id and faculty_id in faculty_data:
            details = faculty_data[faculty_id]
            room["name"] = details["name"]
            room["phone"] = details["phone"]
            room["subject"] = details["subject"]

            photo_filename = details["image"]
            photo_path = os.path.join(PHOTOS_FOLDER, photo_filename)

            if os.path.exists(photo_path):
                room["photo"] = f"/{PHOTOS_FOLDER}/{photo_filename}"
            else:
                room["photo"] = f"/{PHOTOS_FOLDER}/default.jpg"
        else:
            room["name"] = ""
            room["phone"] = ""
            room["subject"] = ""
            room["photo"] = f"/{PHOTOS_FOLDER}/default.jpg"

    return classrooms

# ==============================
# DASHBOARD
@app.route("/dashboard")
def dashboard():
    if "username" not in session:
        if session["role"] == "admin":
            return redirect("/dashboard")
        else:
           return redirect("/faculty_report")
    
    if session["role"] != "admin":
        return "Access Denied", 403   # 🚫 block faculty

    classrooms = load_class_status()
    faculty_data = load_faculty_data()
    classrooms = enrich_class_status(classrooms, faculty_data)

    return render_template("dashboard.html", classrooms=classrooms)
# ==============================
# TIMETABLE
# ==============================
def load_timetable():
    if os.path.exists(TIMETABLE_FILE):
        with open(TIMETABLE_FILE, "r") as f:
            return json.load(f)
    return {}

def save_timetable(data):
    with open(TIMETABLE_FILE, "w") as f:
        json.dump(data, f, indent=4)

@app.route("/timetable")
def timetable():
    if "username" not in session:
        return redirect("/")
    return render_template("timetable.html", timetable=load_timetable())

@app.route("/save_timetable", methods=["POST"])
def save_timetable_route():
    data = load_timetable()
    new_data = {}

    for day, sessions in data.items():
        new_sessions = []
        for idx in range(len(sessions)):
            new_sessions.append({
                "faculty_name": request.form.get(f"{day}-{idx}-faculty"),
                "subject": request.form.get(f"{day}-{idx}-subject"),
                "start_time": request.form.get(f"{day}-{idx}-start"),
                "end_time": request.form.get(f"{day}-{idx}-end"),
                "phone": request.form.get(f"{day}-{idx}-phone")
            })
        new_data[day] = new_sessions

    save_timetable(new_data)
    flash("Timetable updated successfully!")
    return redirect(url_for("timetable"))

# ==============================
# CAPTURE
# ==============================
@app.route("/capture")
def capture():
    if "username" not in session:
        return redirect("/")
    return render_template("capture.html")

# ==============================
# FACULTY DATABASE
# ==============================
@app.route("/faculty_database")
def faculty_database():
    if "username" not in session:
        return redirect("/")

    if os.path.exists(FACULTY_FILE):
        with open(FACULTY_FILE, "r") as f:
            faculty = json.load(f)
    else:
        faculty = {}

    return render_template("faculty_database.html", faculty=faculty)

# ==============================
# FACULTY REPORT + WEEKLY CHART
# ==============================
@app.route("/faculty_report")
def faculty_report():
    if "username" not in session:
        return redirect("/")

    with open(TIMETABLE_FILE) as f:
        timetable = json.load(f)

    try:
        with open("attendance_log.json") as f:
            attendance = json.load(f)
    except:
        attendance = []

    # ===== TABLE REPORT =====
    report = {}

    for day in timetable:
        for cls in timetable[day]:
            name = cls["faculty_name"]
            report.setdefault(name, {"total": 0, "attended": 0})
            report[name]["total"] += 1

    counted = set()

    for record in attendance:
        name = record["faculty_name"]
        key = (name, record["time"][:10])

        if key not in counted:
            counted.add(key)
            report.setdefault(name, {"total": 0, "attended": 0})
            report[name]["attended"] += 1

    for name in report:
        total = report[name]["total"]
        attended = report[name]["attended"]
        report[name]["percentage"] = round((attended / total) * 100, 2) if total > 0 else 0

    # ===== WEEKLY CHART DATA =====
    faculty_weekly = {}

    for record in attendance:
        try:
            name = record["faculty_name"]
            dt = datetime.strptime(record["time"], "%Y-%m-%d %H:%M:%S")
            day = dt.strftime("%A")

            if name not in faculty_weekly:
                faculty_weekly[name] = {
                    "Monday": 0, "Tuesday": 0, "Wednesday": 0,
                    "Thursday": 0, "Friday": 0, "Saturday": 0
                }

            if day in faculty_weekly[name]:
                faculty_weekly[name][day] += 1

        except:
            continue

    # ===== ROLE FILTER =====
    if session["role"] == "faculty":
        username = session["username"]

        report = {
            username: report.get(username, {"total": 0, "attended": 0, "percentage": 0})
        }

        faculty_weekly = {
            username: faculty_weekly.get(username, {
                "Monday": 0, "Tuesday": 0, "Wednesday": 0,
                "Thursday": 0, "Friday": 0, "Saturday": 0
            })
        }


    return render_template(
    "faculty_report.html",
    report=report,
    chart_labels=json.dumps(list(report.keys())),
    chart_data=json.dumps([data["percentage"] for data in report.values()])
)
# ==============================
# LOGOUT
# ==============================
@app.route("/save_faculty", methods=["POST"])
def save_faculty():
    try:
        faculty_id = request.form.get("facultyId")
        name = request.form.get("fullName")
        phone = request.form.get("phone")
        subject = request.form.get("subject")
        captured_img = request.form.get("capturedImg")
        uploaded_photo = request.files.get("uploadedPhoto")

        if not faculty_id:
            return jsonify({"message": "Faculty ID missing"}), 400

        # ✅ Ensure folder exists
        os.makedirs(PHOTOS_FOLDER, exist_ok=True)

        # Load existing data
        if os.path.exists(FACULTY_FILE):
            with open(FACULTY_FILE, "r") as f:
                faculty = json.load(f)
        else:
            faculty = {}

        # ===== SAVE IMAGE =====
        filename = f"{faculty_id}.jpg"
        file_path = os.path.join(PHOTOS_FOLDER, filename)

        # Priority 1: Uploaded file
        if uploaded_photo and uploaded_photo.filename != "":
            uploaded_photo.save(file_path)

        # Priority 2: Captured webcam image
        elif captured_img:
            try:
                header, encoded = captured_img.split(",", 1)
                image_data = base64.b64decode(encoded)

                with open(file_path, "wb") as f:
                    f.write(image_data)
            except Exception as img_error:
                print("IMAGE ERROR:", img_error)
                return jsonify({"message": "Image processing failed"}), 500

        else:
            filename = "default.jpg"

        # ===== SAVE DATA =====
        faculty[faculty_id] = {
            "name": name,
            "phone": phone,
            "subject": subject,
            "image": filename
        }

        with open(FACULTY_FILE, "w") as f:
            json.dump(faculty, f, indent=4)

        return jsonify({"message": "✅ Faculty saved successfully!"})

    except Exception as e:
        print("SAVE ERROR:", e)
        return jsonify({"message": f"❌ Error: {str(e)}"}), 500
@app.route("/update_faculty_database_with_photo", methods=["POST"])
def update_faculty_database_with_photo():
    try:
        faculty_id = request.form.get("facultyId")
        name = request.form.get("name")
        phone = request.form.get("phone")
        subject = request.form.get("subject")
        photo = request.files.get("uploadedPhoto")

        if not faculty_id:
            return jsonify({"error": "Faculty ID missing"}), 400

        # Load existing data
        if os.path.exists(FACULTY_FILE):
            with open(FACULTY_FILE, "r") as f:
                faculty = json.load(f)
        else:
            faculty = {}

        # Handle image upload
        filename = faculty.get(faculty_id, {}).get("image", "default.jpg")

        if photo and photo.filename != "":
            filename = secure_filename(f"{faculty_id}.jpg")
            photo.save(os.path.join(PHOTOS_FOLDER, filename))

        # Update data
        faculty[faculty_id] = {
            "name": name,
            "phone": phone,
            "subject": subject,
            "image": filename
        }

        with open(FACULTY_FILE, "w") as f:
            json.dump(faculty, f, indent=4)

        return jsonify({"message": "Saved successfully"})

    except Exception as e:
        print("ERROR:", e)
        return jsonify({"error": str(e)}), 500
@app.route("/delete_faculty", methods=["POST"])
def delete_faculty():
    try:
        data = request.get_json()
        fid = data.get("facultyId")

        if not fid:
            return jsonify({"message": "Invalid ID"}), 400

        if os.path.exists(FACULTY_FILE):
            with open(FACULTY_FILE, "r") as f:
                faculty = json.load(f)
        else:
            faculty = {}

        if fid in faculty:
            del faculty[fid]

            with open(FACULTY_FILE, "w") as f:
                json.dump(faculty, f, indent=4)

            return jsonify({"message": "Deleted successfully"})

        return jsonify({"message": "Faculty not found"})

    except Exception as e:
        print("DELETE ERROR:", e)
        return jsonify({"message": "Error deleting faculty"}), 500    
@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")

# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    app.run(debug=True)