"""CRUD routes for drills. Every query is limited to the logged-in user's drills."""

from flask import Blueprint, jsonify, request
from sqlalchemy import func

from extensions import db
from models import CATEGORIES, LEVELS, Drill
from routes.helpers import apply_fields, error, json_body, login_required

drills_bp = Blueprint("drills", __name__, url_prefix="/api")

DRILL_FIELDS = ["name", "description", "category", "skill_level", "default_minutes", "equipment"]


def find_drill(user, drill_id):
    # Filtering by user_id means other people's drills look like they don't exist.
    return Drill.query.filter_by(id=drill_id, user_id=user.id).first()


def name_taken(user, name, ignore_id=None):
    query = Drill.query.filter(Drill.user_id == user.id, func.lower(Drill.name) == name.strip().lower())
    if ignore_id is not None:
        query = query.filter(Drill.id != ignore_id)
    return query.first() is not None


@drills_bp.get("/drills")
@login_required
def list_drills(user):
    query = Drill.query.filter_by(user_id=user.id)

    category = request.args.get("category")
    if category:
        query = query.filter(Drill.category == category)
    level = request.args.get("skill_level")
    if level:
        query = query.filter(Drill.skill_level == level)
    search = (request.args.get("q") or "").strip()
    if search:
        query = query.filter(Drill.name.ilike(f"%{search}%"))

    drills = query.order_by(func.lower(Drill.name)).all()
    return jsonify({"drills": [drill.to_dict() for drill in drills]}), 200


@drills_bp.get("/drill-options")
@login_required
def drill_options(user):
    """The allowed categories and levels, so the frontend never hard-codes them."""
    return jsonify({"categories": CATEGORIES, "skill_levels": LEVELS}), 200


@drills_bp.post("/drills")
@login_required
def create_drill(user):
    data = json_body()
    if data is None:
        return error("Request body must be JSON.", 400)

    try:
        drill = Drill(user_id=user.id)
        apply_fields(drill, data, DRILL_FIELDS)
        if drill.name is None:
            raise ValueError("Name is required.")
    except ValueError as problem:
        return error(str(problem), 422)

    if name_taken(user, drill.name):
        return error("You already have a drill with that name.", 409)

    db.session.add(drill)
    db.session.commit()
    return jsonify({"drill": drill.to_dict()}), 201


@drills_bp.get("/drills/<int:drill_id>")
@login_required
def get_drill(user, drill_id):
    drill = find_drill(user, drill_id)
    if drill is None:
        return error("Drill not found.", 404)
    return jsonify({"drill": drill.to_dict()}), 200


@drills_bp.patch("/drills/<int:drill_id>")
@login_required
def update_drill(user, drill_id):
    drill = find_drill(user, drill_id)
    if drill is None:
        return error("Drill not found.", 404)

    data = json_body()
    if data is None:
        return error("Request body must be JSON.", 400)

    try:
        apply_fields(drill, data, DRILL_FIELDS)
    except ValueError as problem:
        db.session.rollback()
        return error(str(problem), 422)

    if name_taken(user, drill.name, ignore_id=drill.id):
        db.session.rollback()
        return error("You already have a drill with that name.", 409)

    db.session.commit()
    return jsonify({"drill": drill.to_dict()}), 200


@drills_bp.delete("/drills/<int:drill_id>")
@login_required
def delete_drill(user, drill_id):
    drill = find_drill(user, drill_id)
    if drill is None:
        return error("Drill not found.", 404)

    db.session.delete(drill)  # also removes it from plans (cascade)
    db.session.commit()
    return "", 204
