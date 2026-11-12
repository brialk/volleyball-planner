"""CRUD routes for practice plans and the drills inside them."""

from flask import Blueprint, jsonify

from extensions import db
from models import Drill, PlanDrill, PracticePlan
from routes.helpers import apply_fields, error, json_body, login_required

plans_bp = Blueprint("plans", __name__, url_prefix="/api")

PLAN_FIELDS = ["title", "focus", "practice_date", "target_minutes", "notes"]
ITEM_FIELDS = ["minutes", "notes"]


def find_plan(user, plan_id):
    return PracticePlan.query.filter_by(id=plan_id, user_id=user.id).first()


def find_item(plan, item_id):
    return next((item for item in plan.items if item.id == item_id), None)


def renumber(plan):
    """Keep positions neat: 1, 2, 3 ... with no gaps."""
    for index, item in enumerate(plan.items, start=1):
        item.position = index


# ---------- plans ----------

@plans_bp.get("/plans")
@login_required
def list_plans(user):
    plans = (
        PracticePlan.query.filter_by(user_id=user.id)
        .order_by(PracticePlan.practice_date.is_(None), PracticePlan.practice_date.desc(), PracticePlan.id.desc())
        .all()
    )
    return jsonify({"plans": [plan.to_dict() for plan in plans]}), 200


@plans_bp.post("/plans")
@login_required
def create_plan(user):
    data = json_body()
    if data is None:
        return error("Request body must be JSON.", 400)

    try:
        plan = PracticePlan(user_id=user.id)
        apply_fields(plan, data, PLAN_FIELDS)
        if plan.title is None:
            raise ValueError("Title is required.")
    except ValueError as problem:
        return error(str(problem), 422)

    db.session.add(plan)
    db.session.commit()
    return jsonify({"plan": plan.to_dict(include_items=True)}), 201


@plans_bp.get("/plans/<int:plan_id>")
@login_required
def get_plan(user, plan_id):
    plan = find_plan(user, plan_id)
    if plan is None:
        return error("Plan not found.", 404)
    return jsonify({"plan": plan.to_dict(include_items=True)}), 200


@plans_bp.patch("/plans/<int:plan_id>")
@login_required
def update_plan(user, plan_id):
    plan = find_plan(user, plan_id)
    if plan is None:
        return error("Plan not found.", 404)

    data = json_body()
    if data is None:
        return error("Request body must be JSON.", 400)

    try:
        apply_fields(plan, data, PLAN_FIELDS)
    except ValueError as problem:
        db.session.rollback()
        return error(str(problem), 422)

    db.session.commit()
    return jsonify({"plan": plan.to_dict(include_items=True)}), 200


@plans_bp.delete("/plans/<int:plan_id>")
@login_required
def delete_plan(user, plan_id):
    plan = find_plan(user, plan_id)
    if plan is None:
        return error("Plan not found.", 404)

    db.session.delete(plan)  # its plan items go too (cascade); the drills stay
    db.session.commit()
    return "", 204


# ---------- drills inside a plan ----------

@plans_bp.post("/plans/<int:plan_id>/items")
@login_required
def add_item(user, plan_id):
    plan = find_plan(user, plan_id)
    if plan is None:
        return error("Plan not found.", 404)

    data = json_body()
    if data is None:
        return error("Request body must be JSON.", 400)

    drill_id = data.get("drill_id")
    drill = None
    if isinstance(drill_id, int) and not isinstance(drill_id, bool):
        drill = Drill.query.filter_by(id=drill_id, user_id=user.id).first()
    if drill is None:
        return error("Choose one of your drills to add.", 422)

    try:
        item = PlanDrill(
            drill=drill,
            position=len(plan.items) + 1,
            minutes=data.get("minutes", drill.default_minutes),  # default to the drill's usual time
        )
        apply_fields(item, data, ["notes"])
    except ValueError as problem:
        db.session.rollback()
        return error(str(problem), 422)

    plan.items.append(item)
    db.session.commit()
    return jsonify({"plan": plan.to_dict(include_items=True)}), 201


@plans_bp.patch("/plans/<int:plan_id>/items/<int:item_id>")
@login_required
def update_item(user, plan_id, item_id):
    plan = find_plan(user, plan_id)
    item = find_item(plan, item_id) if plan else None
    if item is None:
        return error("Plan item not found.", 404)

    data = json_body()
    if data is None:
        return error("Request body must be JSON.", 400)

    try:
        apply_fields(item, data, ITEM_FIELDS)
    except ValueError as problem:
        db.session.rollback()
        return error(str(problem), 422)

    db.session.commit()
    return jsonify({"plan": plan.to_dict(include_items=True)}), 200


@plans_bp.delete("/plans/<int:plan_id>/items/<int:item_id>")
@login_required
def delete_item(user, plan_id, item_id):
    plan = find_plan(user, plan_id)
    item = find_item(plan, item_id) if plan else None
    if item is None:
        return error("Plan item not found.", 404)

    plan.items.remove(item)  # delete-orphan removes the row
    db.session.flush()
    renumber(plan)
    db.session.commit()
    return jsonify({"plan": plan.to_dict(include_items=True)}), 200


@plans_bp.put("/plans/<int:plan_id>/items/order")
@login_required
def reorder_items(user, plan_id):
    """Body: {"item_ids": [3, 1, 2]} = the new order, using every item exactly once."""
    plan = find_plan(user, plan_id)
    if plan is None:
        return error("Plan not found.", 404)

    data = json_body() or {}
    item_ids = data.get("item_ids")
    current_ids = sorted(item.id for item in plan.items)
    if not isinstance(item_ids, list) or sorted(item_ids) != current_ids:
        return error("item_ids must list every drill in the plan exactly once.", 422)

    by_id = {item.id: item for item in plan.items}
    for position, item_id in enumerate(item_ids, start=1):
        by_id[item_id].position = position

    db.session.commit()
    db.session.refresh(plan)  # reload so items come back in the new order
    return jsonify({"plan": plan.to_dict(include_items=True)}), 200
