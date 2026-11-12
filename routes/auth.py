"""Sign up, log in, log out and check who is logged in."""

from flask import Blueprint, jsonify, session
from sqlalchemy import func

from extensions import db
from models import User
from routes.helpers import current_user, error, json_body

auth_bp = Blueprint("auth", __name__, url_prefix="/api")


def start_session(user):
    session.clear()
    session["user_id"] = user.id
    session.permanent = True  # keeps the login after the browser restarts


@auth_bp.post("/signup")
def signup():
    data = json_body()
    if data is None:
        return error("Request body must be JSON.", 400)

    username = data.get("username")
    password = data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return error("Username and password are required.", 422)

    exists = User.query.filter(func.lower(User.username) == username.strip().lower()).first()
    if exists:
        return error("That username is already taken.", 409)

    try:
        user = User(username=username)
        user.password_hash = password
    except ValueError as problem:
        return error(str(problem), 422)

    db.session.add(user)
    db.session.commit()
    start_session(user)
    return jsonify({"user": user.to_dict()}), 201


@auth_bp.post("/login")
def login():
    data = json_body() or {}
    username = data.get("username")
    password = data.get("password")

    user = None
    if isinstance(username, str) and isinstance(password, str):
        user = User.query.filter(func.lower(User.username) == username.strip().lower()).first()

    # Same message for "no such user" and "wrong password" so attackers learn nothing.
    if user is None or not user.authenticate(password):
        return error("Invalid username or password.", 401)

    start_session(user)
    return jsonify({"user": user.to_dict()}), 200


@auth_bp.delete("/logout")
def logout():
    session.clear()
    return "", 204


@auth_bp.get("/check_session")
def check_session():
    """The frontend calls this on page load. Logged out is a normal answer, not an error."""
    user = current_user()
    return jsonify({"user": user.to_dict() if user else None}), 200
