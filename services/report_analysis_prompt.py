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


def build_report_analysis_request(user_id):
    base_prompt = build_llm_prompt(user_id)
    if base_prompt is None:
        return None

    instructions = """
You are a liver report analysis engine.

IMPORTANT:
- Produce consistent results for identical patient data.
- Do not randomly change scores between requests.
- Use only information provided in the patient profile and report history.
- Do not invent missing biomarker values.

Analyze ONLY the most recent report values while using older reports as historical context.

Use the following information:

Patient Factors:
- Age
- Gender
- BMI
- Diabetes
- Hypertension
- Previous liver disease
- Family history
- Activity level
- Exercise frequency
- Alcohol consumption
- Smoking status

Biomarkers:
- AST
- ALT
- Bilirubin
- Albumin
- Platelets
- INR
- PT
- AFP
- HBsAg
- Anti-HCV
- APRI
- FIB-4
- Ultrasound findings

Health Score Guidance:

90-100:
Normal biomarkers with low-risk profile.

75-89:
Minor abnormalities or mild risk factors.

60-74:
Moderate abnormalities or multiple risk factors.

40-59:
Significant abnormalities, fibrosis risk or abnormal imaging.

0-39:
Severe abnormalities or strong evidence of advanced liver disease.

Risk Level:

Low
Moderate
High
Critical

Use the MOST RECENT report values when determining biomarker status.

If historical reports exist:
- Compare current values with previous values.
- Mention whether liver health is improving, worsening or stable.

Biomarker Status Rules:

AST:
- Normal
- Mildly Elevated
- Elevated
- Severely Elevated

ALT:
- Normal
- Mildly Elevated
- Elevated
- Severely Elevated

Bilirubin:
- Normal
- Elevated
- Severely Elevated

Albumin:
- Normal
- Low
- Severely Low

Platelets:
- Normal
- Low
- Severely Low

INR:
- Normal
- Elevated

AFP:
- Normal
- Elevated

APRI:
- Low Risk
- Intermediate Risk
- High Risk

FIB-4:
- Low Risk
- Intermediate Risk
- High Risk

Respond ONLY as a raw JSON object.
Do not include markdown code fences.
Do not include explanations before or after the JSON.
Your entire response must be directly parseable JSON.

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