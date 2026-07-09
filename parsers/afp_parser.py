# parsers/afp_parser.py

import re

def parse_afp(text):

    result = {}

    afp_match = re.search(
        r"(?:ALPHA[\s\-]?FETOPROTEIN|AFP)\s*[:\-]?\s*([\d.]+)",
        text,
        re.IGNORECASE
    )

    if afp_match:
        result["afp"] = float(afp_match.group(1))

    return result