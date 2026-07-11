from flask import Blueprint, request, jsonify

from llm import get_report_analysis

report_analysis_bp = Blueprint(
    "report_analysis",
    __name__
)

@report_analysis_bp.route(
    "/report-analysis",
    methods=["POST"]
)
def report_analysis():

    data = request.get_json()

    user_id = data.get("user_id")

    if not user_id:
        return jsonify({
            "success": False,
            "error": "user_id is required"
        }), 400

    result = get_report_analysis(user_id)

    return jsonify(result)