from db import get_connection

def calculate_health_score(user_row, latest_report=None):

    score = 100

    (
        name,
        age,
        gender,
        weight,
        height,
        bmi,
        diabetes_status,
        hypertension,
        previous_liver_disease,
        family_history,
        activity_level,
        exercise_frequency,
        alcohol_consumption,
        smoking_status
    ) = user_row

    # Lifestyle penalties

    if diabetes_status:
        score -= 10

    if hypertension:
        score -= 5

    if previous_liver_disease:
        score -= 15

    if family_history:
        score -= 5

    if smoking_status == "current":
        score -= 10
    elif smoking_status == "former":
        score -= 5

    if alcohol_consumption == "heavy":
        score -= 15
    elif alcohol_consumption == "moderate":
        score -= 8
    elif alcohol_consumption == "occasional":
        score -= 3

    if bmi is not None:
        if bmi >= 30:
            score -= 10
        elif bmi >= 25:
            score -= 5

    # Biomarker penalties

    if latest_report:

        (
            ast,
            alt,
            bilirubin,
            albumin,
            platelets,
            inr,
            pt,
            afp,
            hbsag,
            anti_hcv,
            apri,
            fib4,
            ultrasound_prediction,
            date_added
        ) = latest_report

        if ast is not None and ast > 40:
            score -= min(15, (ast - 40) / 5)

        if alt is not None and alt > 40:
            score -= min(15, (alt - 40) / 5)

        if bilirubin is not None and bilirubin > 1.2:
            score -= 10

        if albumin is not None and albumin < 3.5:
            score -= 10

        if platelets is not None and platelets < 150:
            score -= 10

        if apri is not None:
            if apri > 1.5:
                score -= 15
            elif apri > 0.7:
                score -= 8

        if fib4 is not None:
            if fib4 > 3.25:
                score -= 15
            elif fib4 > 1.45:
                score -= 8

        if ultrasound_prediction:
            prediction = str(ultrasound_prediction).lower()

            if "cirrhosis" in prediction:
                score -= 25
            elif "fibrosis" in prediction:
                score -= 15
            elif "fatty" in prediction:
                score -= 10

    score = max(0, min(100, round(score)))

    return score

def build_llm_prompt(user_id):
    conn = get_connection()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    name,
                    age,
                    gender,
                    weight,
                    height,
                    bmi,
                    diabetes_status,
                    hypertension,
                    previous_liver_disease,
                    family_history,
                    activity_level,
                    exercise_frequency,
                    alcohol_consumption,
                    smoking_status
                FROM users
                WHERE id=%s
                """,
                (user_id,)
            )
            user_row = cur.fetchone()

            cur.execute(
                """SELECT ast, alt, bilirubin, albumin, platelets, inr, pt,
                    afp, hbsag, anti_hcv, apri, fib4, ultrasound_prediction, date_added
                FROM reports WHERE user_id=%s ORDER BY date_added ASC, id ASC""",
                (user_id,)
            )
            report_rows = cur.fetchall()
    finally:
        conn.close()

    if user_row is None:
        return None

    (
        name,
        user_age,
        gender,
        weight,
        height,
        bmi,
        diabetes_status,
        hypertension,
        previous_liver_disease,
        family_history,
        activity_level,
        exercise_frequency,
        alcohol_consumption,
        smoking_status
    ) = user_row

    latest_report = report_rows[-1] if report_rows else None

    health_score = calculate_health_score(
        user_row,
        latest_report
    )

    def fmt(v):
        return v if v is not None else "N/A"

    prompt = (
        f"Patient Profile:\n"
        f"Name: {name}\n"
        f"Age: {fmt(user_age)}\n"
        f"Gender: {fmt(gender)}\n"
        f"Weight: {fmt(weight)} kg\n"
        f"Height: {fmt(height)} cm\n"
        f"BMI: {fmt(bmi)}\n"
        f"Diabetes: {fmt(diabetes_status)}\n"
        f"Hypertension: {fmt(hypertension)}\n"
        f"Previous Liver Disease: {fmt(previous_liver_disease)}\n"
        f"Family History: {fmt(family_history)}\n"
        f"Activity Level: {fmt(activity_level)}\n"
        f"Exercise Frequency: {fmt(exercise_frequency)}\n"
        f"Alcohol Consumption: {fmt(alcohol_consumption)}\n"
        f"Smoking Status: {fmt(smoking_status)}\n\n"
        f"Precalculated Health Score: {health_score}\n\n"
        f"Liver Panel History (chronological order):\n"
    )

    if not report_rows: 
        prompt += (
            "BIOMARKER_DATA_AVAILABLE: NO\n"
            "No previous reports on record.\n"
        )
    else:
        prompt += "BIOMARKER_DATA_AVAILABLE: YES\n\n"

        for row in report_rows:
            (ast, alt, bilirubin, albumin, platelets, inr, pt,
            afp, hbsag, anti_hcv, apri, fib4, ultrasound_prediction, date_added) = row

            line = (
                f"- {date_added} | AST: {fmt(ast)} U/L, ALT: {fmt(alt)} U/L, "
                f"Bilirubin: {fmt(bilirubin)} mg/dL, Albumin: {fmt(albumin)} g/dL, "
                f"Platelets: {fmt(platelets)}, INR: {fmt(inr)}, PT: {fmt(pt)}, "
                f"AFP: {fmt(afp)}, HBsAg: {fmt(hbsag)}, Anti-HCV: {fmt(anti_hcv)}, "
                f"APRI: {apri if apri is not None else 'insufficient data'}, "
                f"FIB-4: {fib4 if fib4 is not None else 'insufficient data'}, "
                f"Liver Imaging Result: {fmt(ultrasound_prediction)}"
            )

            prompt += line + "\n"

    return prompt


def build_full_llm_request(user_id):
    base_prompt = build_llm_prompt(user_id)
    if base_prompt is None:
        return None

    instructions = """
You are a liver health assessment engine.

IMPORTANT:
The response must be deterministic and consistent.
Given the same input data, always produce approximately the same health score.
Do not randomly adjust scores between requests.

A precalculated health score is provided in the patient profile.

You MUST use that exact score as the value of
"overall_health_score".

Do not recalculate it.
Do not modify it.
Do not increase or decrease it.

ASSESSMENT RULES

STEP 1: Determine whether biomarker data is available.

If the patient has NO laboratory report data:
- Use ONLY onboarding/profile information.
- Do NOT assume any laboratory values.
- Do NOT invent biomarker results.
- Generate a PRELIMINARY BASELINE HEALTH SCORE.

Use the following risk factors:
- Age
- BMI
- Diabetes status
- Hypertension
- Previous liver disease
- Family history
- Activity level
- Exercise frequency
- Alcohol consumption
- Smoking status

When no biomarker data exists:
- AST status must be ""
- ALT status must be ""
- Bilirubin status must be ""
- Albumin status must be ""
- AST value must be "N/A"
- ALT value must be "N/A"
- Bilirubin value must be "N/A"
- Albumin value must be "N/A"

Set:
"apri_fib4_interpretation": "Upload a liver report to calculate APRI and FIB-4 scores."

The AI insights should:
1. Explain the onboarding-based score.
2. Summarize major risk factors.
3. Recommend uploading reports for a more accurate assessment.


STEP 2: If laboratory report data IS available:

Use BOTH:
- Onboarding/profile information
AND
- Biomarker information

Consider:
- AST
- ALT
- Bilirubin
- Albumin
- INR
- PT
- Platelets
- AFP
- HBsAg
- Anti-HCV
- APRI
- FIB-4
- Ultrasound findings

Use the MOST RECENT report values when populating biomarker flags.

Interpretation Rules:
- Higher AST, ALT, Bilirubin, INR and PT decrease the score.
- Lower Albumin decreases the score.
- Higher APRI and FIB-4 decrease the score.
- Abnormal ultrasound findings decrease the score.
- Diabetes, hypertension, smoking, obesity and heavy alcohol use decrease the score.

If multiple reports exist:
- Compare latest report against previous reports.
- Mention whether liver health appears improving, worsening or stable.

IMPORTANT:
For identical patient data, keep the score consistent.
Do not make large score changes unless biomarker values justify them.

Respond with ONLY a raw JSON object.

{
  "overall_health_score": <integer 0-100>,
  "flags": {
    "ast": {
      "status": "<Normal/High/Low or empty string>",
      "value": "<latest value or N/A>"
    },
    "alt": {
      "status": "<Normal/High/Low or empty string>",
      "value": "<latest value or N/A>"
    },
    "bilirubin": {
      "status": "<Normal/High/Low or empty string>",
      "value": "<latest value or N/A>"
    },
    "albumin": {
      "status": "<Normal/High/Low or empty string>",
      "value": "<latest value or N/A>"
    }
  },
  "apri_fib4_interpretation": "<one sentence>",
  "ai_insights": [
    "<insight 1>",
    "<insight 2>",
    "<insight 3>"
  ]
}
"""
    return base_prompt + instructions