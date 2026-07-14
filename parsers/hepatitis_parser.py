import re

def parse_hepatitis(text):
    result = {}

    hbsag_match = re.search(
        r"HBsAg.*?(Reactive|Non[- ]Reactive)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if hbsag_match:

        status = hbsag_match.group(1).lower()

        if "non" in status:
            result["hbsag"] = 0
        else:
            result["hbsag"] = 1

    anti_hcv_match = re.search(
        r"Anti[- ]?HCV.*?(Reactive|Non[- ]Reactive)",
        text,
        re.IGNORECASE | re.DOTALL
    )

    if anti_hcv_match:

        status = anti_hcv_match.group(1).lower()

        if "non" in status:
            result["anti_hcv"] = 0
        else:
            result["anti_hcv"] = 1

    return result