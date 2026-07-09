from flask import Blueprint, request, jsonify
from db import signup, login

auth_bp = Blueprint("auth", __name__)

@auth_bp.route("/signup", methods=["POST"])
def signup_route():

    data = request.get_json()

    user_id = signup(
        data.get("email"),
        data.get("password"),
        data.get("name"),
        data.get("age"),
        data.get("weight"),
        data.get("diabetes_status")
    )

    if user_id is None:
        return jsonify({"error": "Email already exists"}), 400

    return jsonify({"user_id": user_id}), 201


@auth_bp.route("/login", methods=["POST"])
def login_route():

    data = request.get_json()

    user_id = login(
        data.get("email"),
        data.get("password")
    )

    if user_id is None:
        return jsonify({"error": "Invalid credentials"}), 401

    return jsonify({"user_id": user_id}), 200