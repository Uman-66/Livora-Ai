import sqlite3
from datetime import datetime
DB_PATH = "livora.db"

# Set a connection to the SQLite database and enable foreign key support.
def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# Create the users table if it doesn't exist.
def init_db():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            name TEXT,
            age INTEGER,
            weight REAL,
            height REAL,
            bmi REAL,
            diabetes_status TEXT
        )
        """)


# Calcualting BMI (Body Mass Index) based on weight in kilograms and height in centimeters.
def calculate_bmi(weight_kg, height_cm):
    if weight_kg is None or height_cm is None or height_cm <= 0:
        return None
    height_m = height_cm / 100
    return round(weight_kg / (height_m ** 2), 1)

# Creating the reports table if it doesn't exist, with a foreign key reference to the users table.
def init_reports_table():
    with get_connection() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
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
            liv_perfor TEXT,
            date_added TEXT NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users(id)
        )
        """)
def _safe_str(value):
    """Converts extractor/model output to a clean string, or None if missing."""
    if value is None or value == "":
        return None
    return str(value).strip()
def _safe_float(value):
    """Converts extractor output to float, or None if missing/invalid."""
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def _safe_int(value):
    """Converts extractor output to int, or None if missing/invalid."""
    if value is None or value == "":
        return None
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

# Insert a new report into the reports table, handling missing or invalid values gracefully.
def add_report(user_id, age=None, platelets=None, ast=None, alt=None,
               bilirubin=None, albumin=None, inr=None, pt=None,
               afp=None, hbsag=None, anti_hcv=None, ast_uln=40,
               apri=None, fib4=None, liv_perfor=None):
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
    liv_perfor = _safe_str(liv_perfor)

    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute(
                """INSERT INTO reports
                   (user_id, age, platelets, ast, alt, bilirubin, albumin,
                    inr, pt, afp, hbsag, anti_hcv, ast_uln, apri, fib4, liv_perfor, date_added)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (user_id, age, platelets, ast, alt, bilirubin, albumin,
                 inr, pt, afp, hbsag, anti_hcv, ast_uln, apri, fib4, liv_perfor, date_added)
            )
            return cursor.lastrowid
    except sqlite3.Error as e:
        print(f"DB error in add_report: {e}")
        return None
    finally:
        conn.close()

# Signup function to create a new user in the users table, calculating BMI and handling potential integrity errors.
def signup(email, password, name, age, weight, height, diabetes_status):
    bmi = calculate_bmi(weight, height)
    try:
        with get_connection() as conn:
            cursor = conn.execute(
                """INSERT INTO users
                   (email, password, name, age, weight, height, bmi, diabetes_status)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (email, password, name, age, weight, height, bmi, diabetes_status),
            )
            return cursor.lastrowid
    except sqlite3.IntegrityError:
        return None
    finally:
        conn.close()

# Handle login by checking the provided email and password against the stored values in the users table, returning the user ID if successful or None if not.
def login(email, password):
    conn = get_connection()
    try:
        with conn:
            cursor = conn.execute("SELECT id, password FROM users WHERE email=?", (email,))
            row = cursor.fetchone()
    finally:
        conn.close()

    if row is None:
        return None

    user_id, stored_password = row
    if stored_password == password:
        return user_id
    return None



# Build the basic detail about the prompt in loop of the data of patient and the report data in chronological order. If no reports exist, it indicates that this is the patient's first report. The function formats the values, handling None values by displaying "N/A". It constructs a prompt string that includes the patient's profile and liver panel history.
def build_llm_prompt(user_id):
    conn = get_connection()
    try:
        with conn:
            user_row = conn.execute(
                "SELECT name, age, weight, height, bmi, diabetes_status FROM users WHERE id=?",
                (user_id,)
            ).fetchone()

            report_rows = conn.execute(
                """SELECT ast, alt, bilirubin, albumin, platelets, inr, pt,
                    afp, hbsag, anti_hcv, apri, fib4, liv_perfor, date_added
                FROM reports WHERE user_id=? ORDER BY date_added ASC, id ASC""",
                (user_id,)
            ).fetchall()
    finally:
        conn.close()

    if user_row is None:
        return None

    name, user_age, weight, height, bmi, diabetes_status = user_row

    def fmt(v):
        return v if v is not None else "N/A"

    prompt = (
        f"Patient Profile:\n"
        f"Name: {name}, Age: {fmt(user_age)}, Weight: {fmt(weight)}kg, Height: {fmt(height)}cm, "
        f"BMI: {fmt(bmi)}, Diabetes Status: {diabetes_status}\n\n"
        f"Liver Panel History (chronological order):\n"
    )

    if not report_rows:
        prompt += "No previous reports on record. This is the patient's first report.\n"
        return prompt

    for row in report_rows:
        (ast, alt, bilirubin, albumin, platelets, inr, pt,
         afp, hbsag, anti_hcv, apri, fib4, liv_perfor, date_added) = row

        line = (
            f"- {date_added} | AST: {fmt(ast)} U/L, ALT: {fmt(alt)} U/L, "
            f"Bilirubin: {fmt(bilirubin)} mg/dL, Albumin: {fmt(albumin)} g/dL, "
            f"Platelets: {fmt(platelets)}, INR: {fmt(inr)}, PT: {fmt(pt)}, "
            f"AFP: {fmt(afp)}, HBsAg: {fmt(hbsag)}, Anti-HCV: {fmt(anti_hcv)}, "
            f"APRI: {apri if apri is not None else 'insufficient data'}, "
            f"FIB-4: {fib4 if fib4 is not None else 'insufficient data'}, "
            f"Liver Imaging Result: {fmt(liv_perfor)}"
        )
        prompt += line + "\n"

    return prompt

def build_full_llm_request(user_id):
    base_prompt = build_llm_prompt(user_id)
    if base_prompt is None:
        return None

    instructions = """
Use the following liver health scoring criteria when interpreting the patient's data:

Liver Health Score = (Biomarker Score x 35%) + (Fibrosis Score x 25%) + (Ultrasound Score x 20%) + (Comorbidity Score x 10%) + (Metabolic Score x 10%)

Scoring components:
- Liver Function (35%): ALT, AST, AST/ALT ratio, bilirubin, albumin, INR/PT
- Fibrosis Risk (25%): platelet count, FIB-4 score, APRI score, HBsAg, Anti-HCV
- Ultrasound Assessment (20%): normal liver, benign lesion, malignant/suspicious lesion, AFP
- Comorbidities (10%): diabetes, hypertension, previous liver disease, family history
- Metabolic Health (10%): BMI, age, gender

Interpret higher-risk findings as lowering the score and improving values as raising the score. When a component is missing, estimate conservatively and note insufficient data in the explanation.

Respond with ONLY a raw JSON object. Do not include markdown code fences, explanations, or any text before or after the JSON. Your entire response must be valid, directly parseable JSON in exactly this structure:

{
  "overall_health_score": <integer 0-100>,
  "flags": {
    "ast": "<Normal/High/N/A>",
    "alt": "<Normal/High/N/A>",
    "bilirubin": "<Normal/High/N/A>",
    "albumin": "<Normal/Low/N/A>"
  },
  "apri_fib4_interpretation": "<one sentence interpreting the most recent APRI and FIB-4 values if available, otherwise state insufficient data>",
  "ai_insights": [
    "<sentence about the most notable current value>",
    "<sentence comparing to previous record if history exists, otherwise note this is baseline>",
    "<additional relevant insight sentence>"
  ],
  "ai_summary": "<2-3 plain-language sentences a non-medical patient can understand, summarizing what's going on>"
}
"""
    return base_prompt + instructions
init_db()
init_reports_table()

def run_tests():
    print("=" * 60)
    print("TEST SUITE START")
    print("=" * 60)

    test_email = "edgetest@example.com"
    test_password = "testpass123"

    # ---- TEST 1: Fresh signup should succeed ----
    print("\n[Test 1] Fresh signup...")
    user_id = signup(test_email, test_password, "Edge Case Tester", 30, 70.0, 175.0, "None")
    if user_id is not None:
        print(f"  PASS: signup succeeded, user_id={user_id}")
    else:
        print("  User already exists from a previous run, fetching via login instead")
        user_id = login(test_email, test_password)
        if user_id is None:
            print("  FAIL: could not create or find test user, aborting remaining tests")
            return
        print(f"  Using existing user_id={user_id}")

    # ---- TEST 2: Duplicate signup should fail (same email) ----
    print("\n[Test 2] Duplicate signup (same email)...")
    dup = signup(test_email, "differentpass", "Duplicate", 25, 60.0, 165.0, "Type 1")
    print("  PASS: duplicate correctly rejected" if dup is None else f"  FAIL: duplicate allowed, got user_id={dup}")

    # ---- TEST 3: Login with correct password ----
    print("\n[Test 3] Login with correct password...")
    result = login(test_email, test_password)
    print(f"  PASS: login succeeded, user_id={result}" if result == user_id else f"  FAIL: expected {user_id}, got {result}")

    # ---- TEST 4: Login with wrong password ----
    print("\n[Test 4] Login with wrong password...")
    result = login(test_email, "wrongpassword")
    print("  PASS: wrong password correctly rejected" if result is None else f"  FAIL: wrong password accepted, got {result}")

    # ---- TEST 5: Login with nonexistent email ----
    print("\n[Test 5] Login with nonexistent email...")
    result = login("doesnotexist@example.com", "anypassword")
    print("  PASS: nonexistent email correctly rejected" if result is None else f"  FAIL: got {result}")

    # ---- TEST 6: BMI calculation edge cases ----
    print("\n[Test 6] BMI edge cases...")
    bmi_normal = calculate_bmi(70.0, 175.0)
    print(f"  Normal case -> BMI={bmi_normal}", "PASS" if bmi_normal is not None else "FAIL")

    bmi_zero_height = calculate_bmi(70.0, 0)
    print(f"  Zero height -> {bmi_zero_height}", "PASS" if bmi_zero_height is None else "FAIL")

    bmi_none_weight = calculate_bmi(None, 175.0)
    print(f"  None weight -> {bmi_none_weight}", "PASS" if bmi_none_weight is None else "FAIL")

    bmi_negative_height = calculate_bmi(70.0, -10)
    print(f"  Negative height -> {bmi_negative_height}", "PASS" if bmi_negative_height is None else "FAIL")

    # ---- TEST 7: add_report inserts using TODAY's date ----
    print("\n[Test 7] add_report inserts today's date...")
    report_id = add_report(
        user_id=user_id, age=30, platelets=200.0, ast=35.0, alt=40.0,
        bilirubin=0.9, albumin=4.2, inr=1.0, pt=12.0, afp=3.5,
        hbsag=0, anti_hcv=0, ast_uln=40, liv_perfor="Normal"
    )
    if report_id is not None:
        conn = get_connection()
        row = conn.execute("SELECT date_added FROM reports WHERE id=?", (report_id,)).fetchone()
        conn.close()
        stored_date = row[0].split(" ")[0]
        today_str = datetime.now().strftime("%Y-%m-%d")
        print(f"  Stored date: {stored_date} | Today: {today_str}")
        print("  PASS: date matches today" if stored_date == today_str else "  FAIL: date does not match today")
    else:
        print("  FAIL: report insert failed")

    # ---- TEST 8: add_report with all fields missing (should still insert, all None) ----
    print("\n[Test 8] add_report with all fields missing...")
    report_id_empty = add_report(user_id=user_id)
    print(f"  {'PASS' if report_id_empty is not None else 'FAIL'}: report_id={report_id_empty} (nulls allowed)")

    if report_id_empty is not None:
        conn = get_connection()
        row = conn.execute("SELECT liv_perfor FROM reports WHERE id=?", (report_id_empty,)).fetchone()
        conn.close()
        print(f"  liv_perfor stored as: {row[0]}", "PASS: None as expected" if row[0] is None else "FAIL: expected None")

    # ---- TEST 9: add_report with garbage/invalid types (should not crash, should store None) ----
    print("\n[Test 9] add_report with invalid/garbage input types...")
    report_id_garbage = add_report(
        user_id=user_id,
        age="not_a_number",
        platelets="abc",
        ast="",
        alt=None,
        hbsag="maybe",
        liv_perfor=""
    )
    print(f"  {'PASS: did not crash' if report_id_garbage is not None else 'FAIL: insert failed'}, report_id={report_id_garbage}")

    if report_id_garbage is not None:
        conn = get_connection()
        row = conn.execute("SELECT liv_perfor FROM reports WHERE id=?", (report_id_garbage,)).fetchone()
        conn.close()
        print(f"  Empty string liv_perfor stored as: {row[0]}", "PASS: None as expected" if row[0] is None else "FAIL: expected None for empty string")

    # ---- TEST 10: add_report with invalid user_id (foreign key violation) ----
    print("\n[Test 10] add_report with nonexistent user_id (FK constraint)...")
    bad_report = add_report(user_id=999999, ast=40.0)
    print("  PASS: FK constraint correctly blocked insert" if bad_report is None else f"  FAIL: insert succeeded with bad user_id, got {bad_report}")

    # ---- TEST 11: add_report with liv_perfor containing extra whitespace ----
    print("\n[Test 11] add_report strips whitespace from liv_perfor...")
    report_id_ws = add_report(user_id=user_id, ast=30.0, liv_perfor="  Malignant  ")
    if report_id_ws is not None:
        conn = get_connection()
        row = conn.execute("SELECT liv_perfor FROM reports WHERE id=?", (report_id_ws,)).fetchone()
        conn.close()
        print(f"  Stored value: '{row[0]}'", "PASS: whitespace stripped" if row[0] == "Malignant" else "FAIL: whitespace not stripped correctly")
    else:
        print("  FAIL: insert failed")

    # ---- TEST 12: build_llm_prompt for user with reports ----
    print("\n[Test 12] build_llm_prompt for user WITH reports...")
    prompt = build_llm_prompt(user_id)
    has_history = prompt is not None and "Liver Panel History" in prompt and "No previous reports" not in prompt
    print(f"  {'PASS: prompt includes report history' if has_history else 'FAIL: prompt missing expected history section'}")

    # ---- TEST 13: build_llm_prompt includes liv_perfor in output ----
    print("\n[Test 13] build_llm_prompt includes Liver Imaging Result field...")
    has_liv_perfor = prompt is not None and "Liver Imaging Result" in prompt
    print("  PASS: liv_perfor field present in prompt text" if has_liv_perfor else "  FAIL: liv_perfor field missing from prompt")

    # ---- TEST 14: build_llm_prompt includes the actual value we inserted (e.g. 'Normal' or 'Malignant') ----
    print("\n[Test 14] build_llm_prompt includes an actual liv_perfor value (not just N/A)...")
    has_real_value = prompt is not None and ("Normal" in prompt or "Malignant" in prompt)
    print("  PASS: real liv_perfor value found in prompt" if has_real_value else "  FAIL: only N/A values found, expected at least one real label")

    # ---- TEST 15: build_llm_prompt for nonexistent user ----
    print("\n[Test 15] build_llm_prompt for nonexistent user_id...")
    prompt_missing = build_llm_prompt(999999)
    print("  PASS: returned None for missing user" if prompt_missing is None else f"  FAIL: got {prompt_missing}")

    # ---- TEST 16: build_full_llm_request includes JSON instructions ----
    print("\n[Test 16] build_full_llm_request includes JSON schema instructions...")
    full_request = build_full_llm_request(user_id)
    has_json_block = full_request is not None and '"overall_health_score"' in full_request
    print(f"  {'PASS' if has_json_block else 'FAIL'}")

    print("\n" + "=" * 60)
    print("TEST SUITE COMPLETE")
    print("=" * 60)


if __name__ == "__main__":
    run_tests()







if __name__ == "__main__":
    run_tests()