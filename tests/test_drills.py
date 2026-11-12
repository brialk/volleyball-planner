from tests.conftest import make_drill


def test_create_and_list_drill(auth_client):
    drill = make_drill(auth_client, equipment="  cones  ")
    assert drill["equipment"] == "cones"
    listed = auth_client.get("/api/drills").get_json()["drills"]
    assert [d["name"] for d in listed] == ["Partner Passing"]


def test_drill_validation(auth_client):
    def post(**body):
        return auth_client.post("/api/drills", json=body)

    assert post(category="Passing").status_code == 422                     # missing name
    assert post(name="   ").status_code == 422                             # blank name
    assert post(name="A", category="Dancing").status_code == 422           # bad category
    assert post(name="A", skill_level="Pro").status_code == 422            # bad level
    assert post(name="A", default_minutes=0).status_code == 422            # too small
    assert post(name="A", default_minutes=500).status_code == 422          # too big
    assert post(name="A", default_minutes="abc").status_code == 422        # not a number
    assert post(name="x" * 81).status_code == 422                          # too long
    assert auth_client.get("/api/drills").get_json()["drills"] == []       # nothing was saved


def test_duplicate_drill_name_conflict(auth_client):
    make_drill(auth_client, "Wall Setting")
    response = auth_client.post("/api/drills", json={"name": "wall setting"})
    assert response.status_code == 409


def test_filtering_and_search(auth_client):
    make_drill(auth_client, "Target Serving", category="Serving", skill_level="Beginner")
    make_drill(auth_client, "Jump Serve Power", category="Serving", skill_level="Advanced")
    make_drill(auth_client, "Wall Setting", category="Setting")

    def names(query):
        return [d["name"] for d in auth_client.get(f"/api/drills{query}").get_json()["drills"]]

    assert names("?category=Serving") == ["Jump Serve Power", "Target Serving"]
    assert names("?skill_level=Advanced") == ["Jump Serve Power"]
    assert names("?q=wall") == ["Wall Setting"]
    assert names("?category=Serving&q=target") == ["Target Serving"]


def test_update_drill(auth_client):
    drill = make_drill(auth_client)
    response = auth_client.patch(f"/api/drills/{drill['id']}", json={"default_minutes": 20, "name": "Pass Pairs"})
    assert response.status_code == 200
    assert response.get_json()["drill"]["default_minutes"] == 20
    assert auth_client.get(f"/api/drills/{drill['id']}").get_json()["drill"]["name"] == "Pass Pairs"


def test_failed_update_changes_nothing(auth_client):
    drill = make_drill(auth_client)
    assert auth_client.patch(f"/api/drills/{drill['id']}", json={"name": "New", "default_minutes": 999}).status_code == 422
    assert auth_client.get(f"/api/drills/{drill['id']}").get_json()["drill"]["name"] == "Partner Passing"


def test_rename_to_existing_name_conflicts(auth_client):
    make_drill(auth_client, "One")
    two = make_drill(auth_client, "Two")
    assert auth_client.patch(f"/api/drills/{two['id']}", json={"name": "one"}).status_code == 409
    assert auth_client.patch(f"/api/drills/{two['id']}", json={"name": "Two"}).status_code == 200  # same name is fine


def test_delete_drill(auth_client):
    drill = make_drill(auth_client)
    assert auth_client.delete(f"/api/drills/{drill['id']}").status_code == 204
    assert auth_client.get(f"/api/drills/{drill['id']}").status_code == 404
    assert auth_client.delete(f"/api/drills/{drill['id']}").status_code == 404


def test_users_cannot_see_or_change_each_others_drills(auth_client, other_client):
    drill = make_drill(auth_client)
    assert other_client.get("/api/drills").get_json()["drills"] == []
    assert other_client.get(f"/api/drills/{drill['id']}").status_code == 404
    assert other_client.patch(f"/api/drills/{drill['id']}", json={"name": "Hacked"}).status_code == 404
    assert other_client.delete(f"/api/drills/{drill['id']}").status_code == 404
    assert auth_client.get(f"/api/drills/{drill['id']}").get_json()["drill"]["name"] == "Partner Passing"
