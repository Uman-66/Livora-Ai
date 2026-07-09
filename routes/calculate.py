from flask import Blueprint, request, jsonify

from models.patient_data import patient_data

from calculators.fib4 import calculate_fib4
from calculators.apri import calculate_apri

calculate_bp = Blueprint("calculate", __name__)


@calculate_bp.route("/calculate", methods=["POST"])
def calculate():

    try:

        data = request.get_json()

        user_id = int(data["user_id"])

        age = float(data["age"])
        ast_uln = float(data["ast_uln"])

        required_fields = [
            "ast",
            "alt",
            "platelets"
        ]

        missing_fields = [
            field
            for field in required_fields
            if field not in patient_data
        ]

        if missing_fields:

            return jsonify({
                "success": False,
                "missing_fields": missing_fields
            }), 400

        fib4_score = calculate_fib4(
            age=age,
            ast=patient_data["ast"],
            alt=patient_data["alt"],
            platelets=patient_data["platelets"]
        )

        apri_score = calculate_apri(
            ast=patient_data["ast"],
            ast_uln=ast_uln,
            platelets=patient_data["platelets"]
        )

        patient_data["fib4"] = round(fib4_score, 2)
        patient_data["apri"] = round(apri_score, 2)

        report_data = {
            "user_id": user_id,
            "age": age,
            "ast_uln": ast_uln,
            "platelets": patient_data.get("platelets"),
            "ast": patient_data.get("ast"),
            "alt": patient_data.get("alt"),
            "total_bilirubin": patient_data.get("total_bilirubin"),
            "albumin": patient_data.get("albumin"),
            "inr": patient_data.get("inr"),
            "pt": patient_data.get("pt"),
            "afp": patient_data.get("afp"),
            "hbsag": patient_data.get("hbsag"),
            "anti_hcv": patient_data.get("anti_hcv"),
            "fib4": round(fib4_score, 2),
            "apri": round(apri_score, 2)
        }

        return jsonify({
            "success": True,
            "report_data": report_data
        })

        return jsonify({
            "success": True,
            "fib4": round(fib4_score, 2),
            "apri": round(apri_score, 2),
            "patient_data": patient_data
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500