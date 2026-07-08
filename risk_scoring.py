def calculate_risk(biomarkers):

    hba1c = biomarkers.get("hba1c")
    fasting = biomarkers.get("fasting_glucose")

    risk = "Low"

    if hba1c:

        if hba1c >= 6.5:
            risk = "High"

        elif hba1c >= 5.7:
            risk = "Moderate"

    if fasting:

        if fasting >= 126:
            risk = "High"

        elif fasting >= 100 and risk == "Low":
            risk = "Moderate"

    return risk