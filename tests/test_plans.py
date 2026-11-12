from tests.conftest import make_drill


def make_plan(client, **extra):
    response = client.post("/api/plans", json={"title": "Tuesday Practice", "target_minutes": 90, **extra})
    assert response.status_code == 201, response.get_json()
    return response.get_json()["plan"]


def add_item(client, plan_id, drill_id, **extra):
    response = client.post(f"/api/plans/{plan_id}/items", json={"drill_id": drill_id, **extra})
    assert response.status_code == 201, response.get_json()
    return response.get_json()["plan"]


def test_create_plan_and_defaults(auth_client):
    plan = make_plan(auth_client, practice_date="2026-11-10", focus="Serving")
    assert plan["practice_date"] == "2026-11-10"
    assert plan["items"] == []
    assert plan["total_minutes"] == 0


def test_plan_validation(auth_client):
    def post(**body):
        return auth_client.post("/api/plans", json=body)

    assert post(focus="x").status_code == 422                       # no title
    assert post(title="  ").status_code == 422
    assert post(title="A", target_minutes=5).status_code == 422     # below 15
    assert post(title="A", target_minutes=400).status_code == 422   # above 300
    assert post(title="A", practice_date="11/10/2026").status_code == 422
    assert post(title="A", practice_date="2026-13-45").status_code == 422
    assert auth_client.get("/api/plans").get_json()["plans"] == []


def test_update_and_delete_plan(auth_client):
    plan = make_plan(auth_client)
    updated = auth_client.patch(f"/api/plans/{plan['id']}", json={"title": "Renamed", "target_minutes": 60, "practice_date": None})
    assert updated.status_code == 200
    assert updated.get_json()["plan"]["title"] == "Renamed"
    assert auth_client.delete(f"/api/plans/{plan['id']}").status_code == 204
    assert auth_client.get(f"/api/plans/{plan['id']}").status_code == 404


def test_add_drill_defaults_to_drill_minutes_and_totals(auth_client):
    plan = make_plan(auth_client)
    passing = make_drill(auth_client, "Passing", default_minutes=12)
    serving = make_drill(auth_client, "Serving", default_minutes=15)

    add_item(auth_client, plan["id"], passing["id"])
    result = add_item(auth_client, plan["id"], serving["id"], minutes=20, notes="Float serves")

    assert [i["drill"]["name"] for i in result["items"]] == ["Passing", "Serving"]
    assert [i["position"] for i in result["items"]] == [1, 2]
    assert [i["minutes"] for i in result["items"]] == [12, 20]
    assert result["total_minutes"] == 32
    assert result["item_count"] == 2
    assert result["items"][1]["notes"] == "Float serves"


def test_same_drill_can_be_used_twice(auth_client):
    plan = make_plan(auth_client)
    drill = make_drill(auth_client)
    add_item(auth_client, plan["id"], drill["id"])
    result = add_item(auth_client, plan["id"], drill["id"])
    assert result["item_count"] == 2


def test_add_item_validation(auth_client, other_client):
    plan = make_plan(auth_client)
    drill = make_drill(auth_client)
    foreign = make_drill(other_client, "Theirs")

    def post(**body):
        return auth_client.post(f"/api/plans/{plan['id']}/items", json=body)

    assert post().status_code == 422                                  # no drill
    assert post(drill_id=9999).status_code == 422                     # no such drill
    assert post(drill_id=foreign["id"]).status_code == 422            # someone else's drill
    assert post(drill_id="1").status_code == 422                      # wrong type
    assert post(drill_id=drill["id"], minutes=0).status_code == 422
    assert post(drill_id=drill["id"], minutes=181).status_code == 422
    assert auth_client.get(f"/api/plans/{plan['id']}").get_json()["plan"]["items"] == []


def test_update_item_minutes_and_notes(auth_client):
    plan = make_plan(auth_client)
    drill = make_drill(auth_client)
    item_id = add_item(auth_client, plan["id"], drill["id"])["items"][0]["id"]

    response = auth_client.patch(f"/api/plans/{plan['id']}/items/{item_id}", json={"minutes": 25, "notes": "Slow tempo"})
    assert response.status_code == 200
    item = response.get_json()["plan"]["items"][0]
    assert (item["minutes"], item["notes"]) == (25, "Slow tempo")

    assert auth_client.patch(f"/api/plans/{plan['id']}/items/{item_id}", json={"minutes": 0}).status_code == 422
    assert auth_client.patch(f"/api/plans/{plan['id']}/items/99999", json={"minutes": 5}).status_code == 404


def test_remove_item_renumbers_positions(auth_client):
    plan = make_plan(auth_client)
    ids = [make_drill(auth_client, name)["id"] for name in ("A", "B", "C")]
    for drill_id in ids:
        result = add_item(auth_client, plan["id"], drill_id)
    middle = result["items"][1]["id"]

    response = auth_client.delete(f"/api/plans/{plan['id']}/items/{middle}")
    assert response.status_code == 200
    items = response.get_json()["plan"]["items"]
    assert [i["drill"]["name"] for i in items] == ["A", "C"]
    assert [i["position"] for i in items] == [1, 2]


def test_reorder_items(auth_client):
    plan = make_plan(auth_client)
    for name in ("A", "B", "C"):
        result = add_item(auth_client, plan["id"], make_drill(auth_client, name)["id"])
    a, b, c = [i["id"] for i in result["items"]]

    response = auth_client.put(f"/api/plans/{plan['id']}/items/order", json={"item_ids": [c, a, b]})
    assert response.status_code == 200
    assert [i["drill"]["name"] for i in response.get_json()["plan"]["items"]] == ["C", "A", "B"]

    for bad in ([a, b], [a, a, b], [a, b, c, 999], "nope", None):
        assert auth_client.put(f"/api/plans/{plan['id']}/items/order", json={"item_ids": bad}).status_code == 422


def test_deleting_a_drill_removes_it_from_plans(auth_client):
    plan = make_plan(auth_client)
    keep = make_drill(auth_client, "Keep")
    drop = make_drill(auth_client, "Drop")
    add_item(auth_client, plan["id"], keep["id"])
    add_item(auth_client, plan["id"], drop["id"])

    assert auth_client.delete(f"/api/drills/{drop['id']}").status_code == 204
    fresh = auth_client.get(f"/api/plans/{plan['id']}").get_json()["plan"]
    assert [i["drill"]["name"] for i in fresh["items"]] == ["Keep"]


def test_deleting_a_plan_keeps_the_drills(auth_client):
    plan = make_plan(auth_client)
    drill = make_drill(auth_client)
    add_item(auth_client, plan["id"], drill["id"])
    assert auth_client.delete(f"/api/plans/{plan['id']}").status_code == 204
    assert auth_client.get(f"/api/drills/{drill['id']}").status_code == 200


def test_plans_are_private_to_their_owner(auth_client, other_client):
    plan = make_plan(auth_client)
    drill = make_drill(auth_client)
    item_id = add_item(auth_client, plan["id"], drill["id"])["items"][0]["id"]
    url = f"/api/plans/{plan['id']}"

    assert other_client.get("/api/plans").get_json()["plans"] == []
    assert other_client.get(url).status_code == 404
    assert other_client.patch(url, json={"title": "Hacked"}).status_code == 404
    assert other_client.delete(url).status_code == 404
    assert other_client.post(f"{url}/items", json={"drill_id": drill["id"]}).status_code == 404
    assert other_client.patch(f"{url}/items/{item_id}", json={"minutes": 5}).status_code == 404
    assert other_client.delete(f"{url}/items/{item_id}").status_code == 404
    assert other_client.put(f"{url}/items/order", json={"item_ids": [item_id]}).status_code == 404


def test_plan_list_orders_by_date_then_undated_last(auth_client):
    make_plan(auth_client, title="Undated")
    make_plan(auth_client, title="Later", practice_date="2026-12-01")
    make_plan(auth_client, title="Sooner", practice_date="2026-11-20")
    titles = [p["title"] for p in auth_client.get("/api/plans").get_json()["plans"]]
    assert titles == ["Later", "Sooner", "Undated"]
