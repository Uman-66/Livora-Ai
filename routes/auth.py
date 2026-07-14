from flask import Blueprint, request, jsonify

from db import signup, login, update_user_profile


auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/signup", methods=["POST"])
def signup_route():

    data = request.get_json()

    full_name = data.get("full_name")
    email = data.get("email")
    password = data.get("password")
    confirm_password = data.get("confirm_password")


    if not full_name or not email or not password or not confirm_password:
        return jsonify({
            "success": False,
            "error": "full_name, email, password and confirm_password are required"
        }), 400


    if password != confirm_password:
        return jsonify({
            "success": False,
            "error": "Passwords do not match"
        }), 400


    user_id = signup(
        email,
        password,
        full_name,
        
        None,
        None,
        None,
        None,

        None,
        None,
        None,
        None,

        None,
        None,
        None,
        None
    )


    if user_id is None:
        return jsonify({
            "success": False,
            "error": "Email already exists"
        }), 400


    return jsonify({
        "success": True,
        "user_id": user_id
    }), 201



@auth_bp.route("/onboarding", methods=["POST"])
def onboarding():


    data = request.get_json()


    user_id = data.get("user_id")


    if not user_id:
        return jsonify({
            "success": False,
            "error": "user_id is required"
        }),400



    updated = update_user_profile(

        user_id,

        data.get("age"),
        data.get("gender"),
        data.get("weight"),
        data.get("height"),

        data.get("diabetes_status"),
        data.get("hypertension"),
        data.get("previous_liver_disease"),
        data.get("family_history"),

        data.get("activity_level"),
        data.get("exercise_frequency"),
        data.get("alcohol_consumption"),
        data.get("smoking_status")
    )


    if not updated:
        return jsonify({
            "success":False,
            "error":"Could not update profile"
        }),500


    return jsonify({
        "success":True,
        "message":"Onboarding completed"
    }),200



@auth_bp.route("/login", methods=["POST"])
def login_route():

    data=request.get_json()

    user = login(
        data.get("email"),
        data.get("password")
    )

    if user is None:
        return jsonify({
            "success": False,
            "error": "Invalid credentials"
        }), 401
    
    return jsonify({
        "success": True,
        "user": user
    }), 200