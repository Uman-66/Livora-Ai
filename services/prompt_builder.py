from db import get_connection

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
        f"Liver Panel History (chronological order):\n"
    )

    if not report_rows:
        prompt += "No previous reports on record. This is the patient's first report.\n"
        return prompt

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
Use the following liver health scoring criteria when interpreting the patient's data:

Liver Health Score = (Biomarker Score x 35%) + (Fibrosis Score x 25%) + (Ultrasound Score x 25%) + (Comorbidity Score x 3%) + (Metabolic Score x 12%)

Scoring components:
- Liver Function (35%): ALT, AST, AST/ALT ratio, bilirubin, albumin, INR/PT
- Fibrosis Risk (25%): platelet count, FIB-4 score, APRI score, HBsAg, Anti-HCV
- Ultrasound Assessment (20%): Normal liver, HCC, Hemangioma
- Comorbidities (10%): diabetes, hypertension, previous liver disease, family history
- Metabolic Health (10%): BMI, age

Interpret higher-risk findings as lowering the score and improving values as raising the score. When a component is missing, estimate conservatively and note insufficient data in the explanation.

Respond with ONLY a raw JSON object. Do not include markdown code fences, explanations, or any text before or after the JSON. Your entire response must be valid, directly parseable JSON in exactly this structure:

{
  "overall_health_score": <integer 0-100>,
  "flags": {
    "ast": {
      "status": "<Normal/High/N/A>",
      "value": "<latest AST value>"
    },
    "alt": {
      "status": "<Normal/High/N/A>",
      "value": "<latest ALT value>"
    },
    "bilirubin": {
      "status": "<Normal/High/N/A>",
      "value": "<latest bilirubin value>"
    },
    "albumin": {
      "status": "<Normal/Low/N/A>",
      "value": "<latest albumin value>"
    }
  },
  "apri_fib4_interpretation": "<one sentence interpreting the most recent APRI and FIB-4 values if available, otherwise state insufficient data>",
  "ai_insights": [
    "<sentence about the most notable current value>",
    "<sentence comparing to previous record if history exists, otherwise note this is baseline>",
    "<additional relevant insight sentence>"
  ]
}
"""
    return base_prompt + instructions