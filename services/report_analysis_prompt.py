from db import get_connection

def build_llm_prompt(user_id):
    conn = get_connection()
    try:
        with conn:
            user_row = conn.execute(
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
                WHERE id=?
                """,
                (user_id,)
            ).fetchone()
            
            report_rows = conn.execute(
                """SELECT ast, alt, bilirubin, albumin, platelets, inr, pt,
                    afp, hbsag, anti_hcv, apri, fib4, ultrasound_prediction, date_added
                FROM reports WHERE user_id=? ORDER BY date_added ASC, id ASC""",
                (user_id,)
            ).fetchall()
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


def build_report_analysis_request(user_id):
    base_prompt = build_llm_prompt(user_id)
    if base_prompt is None:
        return None

    instructions = """
Analyze ONLY the most recent report values while using older reports as historical context.

When determining overall health score and risk level, consider:

- Current biomarkers
- Biomarker trends over time
- BMI
- Age
- Gender
- Diabetes
- Hypertension
- Previous liver disease
- Family history
- Activity level
- Exercise frequency
- Alcohol consumption
- Smoking status

Heavy alcohol use, smoking, obesity, diabetes,
hypertension, previous liver disease and abnormal
ultrasound findings should increase risk level.

Determine:

1. Overall liver health score (0-100)
2. Risk level:
   - Low
   - Moderate
   - High
   - Critical

3. Biomarker status for:
   AST
   ALT
   Bilirubin
   Albumin
   Platelets
   INR
   AFP

For each biomarker provide:
- value
- status

Status examples:
- Normal
- Mildly Elevated
- Elevated
- Severely Elevated
- Low
- Severely Low
- N/A

Also generate a patient-friendly explanation for every available biomarker.

Respond ONLY as valid JSON.

{
  "overall_health_score": <integer>,
  "risk_level": "<Low/Moderate/High/Critical>",

  "biomarker_status": {
    "ast": {
      "value": "<value>",
      "status": "<status>"
    },
    "alt": {
      "value": "<value>",
      "status": "<status>"
    },
    "bilirubin": {
      "value": "<value>",
      "status": "<status>"
    },
    "albumin": {
      "value": "<value>",
      "status": "<status>"
    },
    "platelets": {
      "value": "<value>",
      "status": "<status>"
    },
    "inr": {
      "value": "<value>",
      "status": "<status>"
    },
    "afp": {
      "value": "<value>",
      "status": "<status>"
    },
    "apri": {
    "value": "<value>",
    "status": "<status>"
    },
    "fib4": {
    "value": "<value>",
    "status": "<status>"
    }
  },

  "biomarker_insights": [
    {
      "biomarker": "<name>",
      "value": "<value>",
      "insight": "<patient-friendly explanation>"
    }
  ],

  "ai_summary": "<3-5 sentence summary>"
}
"""
    return base_prompt + instructions