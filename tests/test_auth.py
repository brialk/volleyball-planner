from tests.conftest import signup


def test_signup_logs_you_in(client):
    response = signup(client)
    assert response.status_code == 201
    assert response.get_json()["user"]["username"] == "alex"
    assert client.get("/api/check_session").get_json()["user"]["username"] == "alex"


def test_signup_response_never_contains_password(client):
    body = signup(client).get_json()
    assert "password" not in str(body).lower()


def test_signup_validation(client):
    assert client.post("/api/signup", json={"username": "ab", "password": "password123"}).status_code == 422
    assert client.post("/api/signup", json={"username": "good_name", "password": "short"}).status_code == 422
    assert client.post("/api/signup", json={"username": "bad name!", "password": "password123"}).status_code == 422
    assert client.post("/api/signup", json={"username": "alex"}).status_code == 422
    assert client.post("/api/signup", data="not json").status_code == 400


def test_duplicate_username_is_rejected_case_insensitively(client, app):
    signup(client, "Alex")
    other = app.test_client()
    assert signup(other, "alex").status_code == 409


def test_login_logout_flow(client):
    signup(client)
    assert client.delete("/api/logout").status_code == 204
    assert client.get("/api/check_session").get_json()["user"] is None

    assert client.post("/api/login", json={"username": "alex", "password": "wrong-pass"}).status_code == 401
    assert client.post("/api/login", json={"username": "nobody", "password": "password123"}).status_code == 401
    ok = client.post("/api/login", json={"username": "ALEX", "password": "password123"})
    assert ok.status_code == 200
    assert client.get("/api/check_session").get_json()["user"]["username"] == "alex"


def test_protected_routes_require_login(client):
    for method, url in [("get", "/api/drills"), ("post", "/api/drills"), ("get", "/api/plans"), ("post", "/api/plans")]:
        assert getattr(client, method)(url, json={}).status_code == 401


def test_password_is_hashed_in_database(app, client):
    from models import User

    signup(client)
    user = User.query.filter_by(username="alex").first()
    assert user._password_hash != "password123"
    assert user._password_hash.startswith("$2")
    try:
        user.password_hash
        assert False, "should not be readable"
    except AttributeError:
        pass


def test_json_404_for_unknown_api_route(client):
    response = client.get("/api/nope")
    assert response.status_code == 404
    assert response.get_json()["error"]
