from flask import Flask, render_template, request, redirect, session, flash, url_for
import os
import numpy as np

app = Flask(__name__)
app.secret_key = "dermascan_secret_2024"

UPLOAD_FOLDER = "static/uploads/"
MODEL_PATH = "model/vgg16_malignant_vs_benign.h5"
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# ─── Lazy model loading (avoids crash if model not yet placed) ───
model = None

def get_model():
    global model
    if model is None:
        if not os.path.exists(MODEL_PATH):
            raise FileNotFoundError(
                f"Model not found at '{MODEL_PATH}'. "
                "Please place your .h5 file at: Skin cancer App/model/vgg16_malignant_vs_benign.h5"
            )
        from tensorflow.keras.models import load_model
        model = load_model(MODEL_PATH)
    return model


# ─── MySQL setup (optional — falls back gracefully if unavailable) ───
db     = None
cursor = None

try:
    import mysql.connector
    db = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        database="skin_cancer_db"
    )
    cursor = db.cursor(dictionary=True)
except Exception as e:
    print(f"[WARN] DB not connected: {e}. Using in-memory storage.")

# In-memory fallback when DB is unavailable
_mem_patients = []


def db_query(sql, params=(), fetch="all"):
    """Execute a query; return None on failure."""
    if cursor is None:
        return None
    try:
        cursor.execute(sql, params)
        if fetch == "one":
            return cursor.fetchone()
        if fetch == "all":
            return cursor.fetchall()
        if fetch == "commit":
            db.commit()
            return True
    except Exception as e:
        print(f"[DB ERROR] {e}")
        return None


# ════════════════════════════════════════════════════════════
#  AUTH
# ════════════════════════════════════════════════════════════

@app.route('/')
def index():
    return redirect(url_for('login'))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("username", "").strip()
        pwd  = request.form.get("password", "")

        if cursor:
            row = db_query("SELECT * FROM users WHERE username=%s", (user,), fetch="one")
            if not row:
                flash(f"Username '{user}' not found. Create an account.", "warning")
                return redirect(url_for("signup"))
            result = db_query(
                "SELECT * FROM users WHERE username=%s AND password=%s",
                (user, pwd), fetch="one"
            )
            if result:
                session["user"] = result["username"]
                session["role"] = result.get("role", "Doctor")
                return redirect(url_for("dashboard"))
            else:
                flash("Incorrect password.", "danger")
        else:
            # Demo mode: accept any credentials
            session["user"] = user
            session["role"] = "Doctor (Demo)"
            flash("Running in demo mode — DB not connected.", "warning")
            return redirect(url_for("dashboard"))

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        first_name  = request.form.get("first_name", "").strip()
        last_name   = request.form.get("last_name", "").strip()
        username    = request.form.get("username", "").strip()
        email       = request.form.get("email", "").strip().lower()
        role        = request.form.get("role", "Doctor").strip()
        pwd         = request.form.get("password", "")
        confirm_pwd = request.form.get("confirm_password", "")

        errors = []
        if not all([first_name, last_name, username, email, pwd]):
            errors.append("All fields are required.")
        if len(username) < 3:
            errors.append("Username must be at least 3 characters.")
        if len(pwd) < 8:
            errors.append("Password must be at least 8 characters.")
        if pwd != confirm_pwd:
            errors.append("Passwords do not match.")

        if cursor:
            if db_query("SELECT id FROM users WHERE username=%s", (username,), fetch="one"):
                errors.append(f"Username '{username}' is already taken.")
            if db_query("SELECT id FROM users WHERE email=%s", (email,), fetch="one"):
                errors.append("Email already associated with an account.")

        if errors:
            for err in errors:
                flash(err, "danger")
            return render_template("signup.html")

        if cursor:
            db_query("""
                INSERT INTO users (username, password, first_name, last_name, email, role)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (username, pwd, first_name, last_name, email, role), fetch="commit")

        session["user"] = username
        session["role"] = role
        flash(f"Welcome, {first_name}! Account created.", "success")
        return redirect(url_for("dashboard"))

    return render_template("signup.html")


@app.route("/forgot-password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        flash("If this email is linked to an account, a reset link has been sent.", "success")
        return redirect(url_for("forgot_password"))
    return render_template("forget_password.html")


# ════════════════════════════════════════════════════════════
#  DASHBOARD
# ════════════════════════════════════════════════════════════

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    if cursor:
        patients_count = (db_query("SELECT COUNT(*) AS total FROM patients", fetch="one") or {}).get("total", 0)
        priority_patients = db_query("""
            SELECT name, age, result, probability, image_path FROM patients
            WHERE result = 'Malignant' OR probability >= 0.50
            ORDER BY probability DESC LIMIT 5
        """) or []
        recent_patients = db_query("""
            SELECT name, age, result, probability, image_path FROM patients
            ORDER BY id DESC LIMIT 10
        """) or []
    else:
        patients_count    = len(_mem_patients)
        priority_patients = [p for p in _mem_patients if p["probability"] >= 0.5][:5]
        recent_patients   = list(reversed(_mem_patients))[:10]

    priority_count = len(priority_patients)
    notifications  = []

    if priority_count > 0:
        notifications.append({"title": "AI Priority", "message": f"{priority_count} patient(s) need attention.", "type": "warning", "is_read": False})
    if patients_count > 0:
        notifications.append({"title": "Analyses available", "message": f"{patients_count} patient(s) recorded.", "type": "success", "is_read": False})
    else:
        notifications.append({"title": "Welcome", "message": "Start by adding a first analysis.", "type": "info", "is_read": False})

    notif_unread = sum(1 for n in notifications if not n["is_read"])

    return render_template(
        "dashboard.html",
        analyses_count    = patients_count,
        pending_count     = 0,
        patients_count    = patients_count,
        notifications     = notifications,
        notif_unread      = notif_unread,
        priority_patients = priority_patients,
        recent_patients   = recent_patients,
    )


# ════════════════════════════════════════════════════════════
#  PREDICTION  ← fixed
# ════════════════════════════════════════════════════════════

@app.route("/predict", methods=["GET", "POST"])
def predict():
    if "user" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        try:
            name = request.form.get("name", "").strip()
            age  = request.form.get("age", "").strip()
            file = request.files.get("image")

            if not file or file.filename == "":
                flash("Please select an image.", "warning")
                return redirect(url_for("predict"))

            # Save uploaded file
            filename = file.filename
            path     = os.path.join(app.config["UPLOAD_FOLDER"], filename)
            file.save(path)
            db_path  = "/" + path.replace("\\", "/")

            # ── Image preprocessing ──────────────────────────────
            from tensorflow.keras.preprocessing import image as keras_image

            img = keras_image.load_img(path, target_size=(224, 224))
            img_array = keras_image.img_to_array(img)      # shape (224,224,3)
            img_array = img_array / 255.0                   # normalize to [0,1]
            img_array = np.expand_dims(img_array, axis=0)   # shape (1,224,224,3)

            # ── Run model ────────────────────────────────────────
            mdl   = get_model()
            pred  = mdl.predict(img_array)

            # Handle both binary (shape (1,1)) and softmax (shape (1,2)) outputs
            if pred.shape[-1] == 1:
                probability = float(pred[0][0])
            else:
                probability = float(pred[0][1])   # index 1 = malignant class

            result = "Malignant" if probability > 0.5 else "Benign"

            # ── Persist patient ──────────────────────────────────
            if cursor:
                db_query("""
                    INSERT INTO patients (name, age, result, probability, image_path)
                    VALUES (%s, %s, %s, %s, %s)
                """, (name, age, result, probability, db_path), fetch="commit")
            else:
                _mem_patients.append({
                    "name": name, "age": age, "result": result,
                    "probability": probability, "image_path": db_path,
                })

            flash("Analysis successful ✔ Patient added.", "success")
            return render_template(
                "result.html",
                result = result,
                prob   = round(probability * 100, 1),
                img    = db_path,
                name   = name,
                age    = age,
            )

        except FileNotFoundError as e:
            flash(str(e), "danger")
            return redirect(url_for("predict"))
        except Exception as e:
            import traceback
            traceback.print_exc()
            flash(f"System error: {e}", "danger")
            return redirect(url_for("predict"))

    return render_template("predict.html")


# ════════════════════════════════════════════════════════════
#  OTHER PAGES
# ════════════════════════════════════════════════════════════

@app.route("/patients")
def patients():
    if "user" not in session:
        return redirect(url_for("login"))
    if cursor:
        data = db_query("SELECT * FROM patients ORDER BY id DESC") or []
    else:
        data = list(reversed(_mem_patients))
    return render_template("patients.html", patients=data)


@app.route("/help")
def help_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("help.html")


@app.route("/settings")
def settings():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("settings.html")


@app.route("/notifications")
def notifications_page():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("notifications.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))


if __name__ == "__main__":
    app.run(debug=True)
