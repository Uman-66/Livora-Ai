from flask import Flask, request, jsonify
from db import signup, login  # importing your working functions from last night

app = Flask(__name__)

@app.route("/signup", methods=["POST"])
def signup_route():
    data = request.get_json()  # this reads the JSON body the mobile app sends
    email = data.get("email")
    password = data.get("password")
    name = data.get("name")
    age = data.get("age")
    weight = data.get("weight")
    diabetes_status = data.get("diabetes_status")

    user_id = signup(email, password, name, age, weight, diabetes_status)

    if user_id is None:
        return jsonify({"error": "Email already exists"}), 400
    return jsonify({"user_id": user_id}), 201


@app.route("/login", methods=["POST"])
def login_route():
    data = request.get_json()
    email = data.get("email")
    password = data.get("password")

    user_id = login(email, password)

    if user_id is None:
        return jsonify({"error": "Invalid credentials"}), 401
    return jsonify({"user_id": user_id}), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)