import re

def extract_biomarkers(text):
    biomarkers = {}

    hba1c = re.search(r'HbA1c[:\s]*([\d.]+)', text, re.IGNORECASE)

    if hba1c:
        biomarkers["hba1c"] = float(hba1c.group(1))

    fasting = re.search(
        r'Fasting.*?([\d.]+)',
        text,
        re.IGNORECASE
    )

    if fasting:
        biomarkers["fasting_glucose"] = float(fasting.group(1))

    return biomarkers