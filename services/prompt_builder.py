from db import get_connection

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
                    afp, hbsag, anti_hcv, apri, fib4, ultrasound_prediction, date_added
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
- Ultrasound Assessment (25%): Normal liver, HCC, Hemangioma
- Comorbidities (3%): diabetes, or other relevant conditions
- Metabolic Health (12%): BMI, age

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