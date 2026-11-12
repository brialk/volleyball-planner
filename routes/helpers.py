"""Small helpers shared by every route file."""

from functools import wraps

from flask import jsonify, request, session

from extensions import db
from models import User


def error(message, status):
    """Every error response has the same shape: {"error": "..."}."""
    return jsonify({"error": message}), status


def current_user():
    user_id = session.get("user_id")
    return db.session.get(User, user_id) if user_id else None


def login_required(view):
    """Reject the request with 401 unless someone is logged in."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        user = current_user()
        if user is None:
            session.pop("user_id", None)
            return error("Please log in to continue.", 401)
        return view(user, *args, **kwargs)

    return wrapper


def json_body():
    """Return the JSON body if it is an object, otherwise None."""
    data = request.get_json(silent=True)
    return data if isinstance(data, dict) else None


def apply_fields(model, data, allowed):
    """Copy allowed keys from data onto model. Model validators raise ValueError."""
    for field in allowed:
        if field in data:
            setattr(model, field, data[field])
