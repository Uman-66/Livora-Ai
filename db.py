import psycopg2
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ.get("DATABASE_URL")


def get_connection():
    return psycopg2.connect(DATABASE_URL)


def init_db():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS users (
                id SERIAL PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                password TEXT NOT NULL,
                name TEXT,
                age INTEGER,
                gender TEXT,
                weight REAL,
                height REAL,
                bmi REAL,
                diabetes_status INTEGER DEFAULT 0,
                hypertension INTEGER DEFAULT 0,
                previous_liver_disease INTEGER DEFAULT 0,
                family_history INTEGER DEFAULT 0,
                activity_level TEXT,
                exercise_frequency TEXT,
                alcohol_consumption TEXT,
                smoking_status TEXT
            )
            """)
        conn.commit()


def calculate_bmi(weight_kg, height_cm):
    if weight_kg is None or height_cm is None or height_cm <= 0:
        return None
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)


def init_reports_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS reports (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                age INTEGER,
                platelets REAL,
                ast REAL,
                alt REAL,
                bilirubin REAL,
                albumin REAL,
                inr REAL,
                pt REAL,
                afp REAL,
                hbsag INTEGER,
                anti_hcv INTEGER,
                ast_uln REAL,
                apri REAL,
                fib4 REAL,
                ultrasound_prediction TEXT,
                date_added TEXT NOT NULL
            )
            """)
        conn.commit()


def init_upload_history_table():
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
            CREATE TABLE IF NOT EXISTS upload_history (
                id SERIAL PRIMARY KEY,
                user_id INTEGER NOT NULL REFERENCES users(id),
                report_type TEXT NOT NULL,
                date_uploaded TEXT NOT NULL
            )
            """)
        conn.commit()


def add_uploaded_report(user_id, report_type):
    date_uploaded = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO upload_history (user_id, report_type, date_uploaded)
                   VALUES (%s, %s, %s)""",
                (user_id, report_type, date_uploaded)
            )
        conn.commit()


def get_recent_reports(user_id, limit=3):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """SELECT report_type, date_uploaded
                   FROM upload_history
                   WHERE user_id = %s
                   ORDER BY date_uploaded DESC
                   LIMIT %s""",
                (user_id, limit)
            )
            rows = cur.fetchall()
        return [{"report_type": row[0], "date_uploaded": row[1]} for row in rows]
    finally:
        conn.close()


def _safe_float(value):
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_int(value):
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None


def _safe_str(value):
    if value is None or value == "":
        return None
    return str(value).strip()


def normalize(value):
    if value is None:
        return None
    return str(value).strip().lower()


def _safe_bool(value):
    return 1 if str(value).lower() in ["true", "1", "yes"] else 0


def validate_choice(value, allowed):
    return value if value in allowed else None


def add_report(user_id, age=None, platelets=None, ast=None, alt=None,
               bilirubin=None, albumin=None, inr=None, pt=None,
               afp=None, hbsag=None, anti_hcv=None, ast_uln=40,
               apri=None, fib4=None, ultrasound_prediction=None):
    date_added = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    age = _safe_int(age)
    platelets = _safe_float(platelets)
    ast = _safe_float(ast)
    alt = _safe_float(alt)
    bilirubin = _safe_float(bilirubin)
    albumin = _safe_float(albumin)
    inr = _safe_float(inr)
    pt = _safe_float(pt)
    afp = _safe_float(afp)
    hbsag = _safe_int(hbsag)
    anti_hcv = _safe_int(anti_hcv)
    ast_uln = _safe_float(ast_uln)
    apri = _safe_float(apri)
    fib4 = _safe_float(fib4)
    ultrasound_prediction = _safe_str(ultrasound_prediction)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO reports
                   (user_id, age, platelets, ast, alt, bilirubin, albumin,
                    inr, pt, afp, hbsag, anti_hcv, ast_uln, apri, fib4,
                    ultrasound_prediction, date_added)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (user_id, age, platelets, ast, alt, bilirubin, albumin,
                 inr, pt, afp, hbsag, anti_hcv, ast_uln, apri, fib4,
                 ultrasound_prediction, date_added)
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    except psycopg2.Error as e:
        print(f"DB error in add_report: {e}")
        conn.rollback()
        return None
    finally:
        conn.close()


def signup(email, password, name, age, gender, weight, height, diabetes_status,
           hypertension, previous_liver_disease, family_history, activity_level,
           exercise_frequency, alcohol_consumption, smoking_status):
    bmi = calculate_bmi(weight, height)

    diabetes_status = _safe_bool(diabetes_status)
    hypertension = _safe_bool(hypertension)
    previous_liver_disease = _safe_bool(previous_liver_disease)
    family_history = _safe_bool(family_history)

    activity_level = normalize(activity_level)
    exercise_frequency = normalize(exercise_frequency)
    alcohol_consumption = normalize(alcohol_consumption)
    smoking_status = normalize(smoking_status)

    activity_level = validate_choice(activity_level, ["sedentary", "lightly active", "moderately active", "very active"])
    exercise_frequency = validate_choice(exercise_frequency, ["never", "1-2 times per week", "2-4 times per week", "5+ times every week", "every day"])
    alcohol_consumption = validate_choice(alcohol_consumption, ["none", "occasional", "moderate", "heavy"])
    smoking_status = validate_choice(smoking_status, ["never", "former", "current"])

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """INSERT INTO users
                   (email, password, name, age, gender, weight, height, bmi,
                    diabetes_status, hypertension, previous_liver_disease, family_history,
                    activity_level, exercise_frequency, alcohol_consumption, smoking_status)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                   RETURNING id""",
                (email, password, name, age, gender, weight, height, bmi,
                 diabetes_status, hypertension, previous_liver_disease, family_history,
                 activity_level, exercise_frequency, alcohol_consumption, smoking_status)
            )
            new_id = cur.fetchone()[0]
        conn.commit()
        return new_id
    except psycopg2.IntegrityError:
        conn.rollback()
        return None
    finally:
        conn.close()


def login(email, password):
    conn = get_connection()

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    id,
                    password,
                    name,
                    email,
                    age,
                    gender
                FROM users
                WHERE email=%s
            """, (email,))

            row = cur.fetchone()

    finally:
        conn.close()

    if row is None:
        return None

    (
        user_id,
        stored_password,
        name,
        email,
        age,
        gender
    ) = row

    if stored_password != password:
        return None

    return {
        "user_id": user_id,
        "full_name": name,
        "email": email,
        "age": age,
        "gender": gender
    }

def update_user_profile(user_id, age, gender, weight, height, diabetes_status,
                         hypertension, previous_liver_disease, family_history,
                         activity_level, exercise_frequency, alcohol_consumption,
                         smoking_status):
    bmi = calculate_bmi(weight, height)

    diabetes_status = _safe_bool(diabetes_status)
    hypertension = _safe_bool(hypertension)
    previous_liver_disease = _safe_bool(previous_liver_disease)
    family_history = _safe_bool(family_history)

    activity_level = normalize(activity_level)
    exercise_frequency = normalize(exercise_frequency)
    alcohol_consumption = normalize(alcohol_consumption)
    smoking_status = normalize(smoking_status)

    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """UPDATE users
                   SET age=%s, gender=%s, weight=%s, height=%s, bmi=%s,
                       diabetes_status=%s, hypertension=%s, previous_liver_disease=%s,
                       family_history=%s, activity_level=%s, exercise_frequency=%s,
                       alcohol_consumption=%s, smoking_status=%s
                   WHERE id=%s""",
                (age, gender, weight, height, bmi, diabetes_status, hypertension,
                 previous_liver_disease, family_history, activity_level,
                 exercise_frequency, alcohol_consumption, smoking_status, user_id)
            )
        conn.commit()
        return True
    except psycopg2.Error as e:
        print("Profile update error:", e)
        conn.rollback()
        return False
    finally:
        conn.close()


init_db()
init_reports_table()
init_upload_history_table()