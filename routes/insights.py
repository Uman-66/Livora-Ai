from flask import Blueprint, request, jsonify

from llm import get_liver_analysis

insights_bp = Blueprint("insights", __name__)


@insights_bp.route("/insights", methods=["POST"])
def insights():

    try:

        data = request.get_json()

        user_id = data.get("user_id")

        if not user_id:

            return jsonify({
                "success": False,
                "error": "user_id is required"
            }), 400

        result = get_liver_analysis(user_id)

        return jsonify({
            "success": True,
            "analysis": result
        })

    except Exception as e:

        return jsonify({
            "success": False,
            "error": str(e)
        }), 500