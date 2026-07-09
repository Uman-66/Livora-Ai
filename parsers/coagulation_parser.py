import re

def parse_coagulation(text):

    result = {}

    pt_match = re.search(
        r"Patient\s+Value\s+([\d.]+)\s+seconds",
        text,
        re.IGNORECASE
    )

    if pt_match:
        result["pt"] = float(pt_match.group(1))

    inr_match = re.search(
        r"INR\s+Value\s+([\d.]+)",
        text,
        re.IGNORECASE
    )

    if inr_match:
        result["inr"] = float(inr_match.group(1))

    return result