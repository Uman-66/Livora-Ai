import re

def parse_cbc(text):
    result = {}

    match = re.search(
        r"PLATELET(?:S)?\s*COUNT\s+([\d.]+)",
        text,
        re.IGNORECASE
    )

    if match:
        platelets = float(match.group(1))

        if platelets > 10000:
            platelets = platelets / 1000

        result["platelets"] = platelets

    return result