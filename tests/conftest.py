import pytest

from app import create_app
from extensions import db


class TestConfig:
    TESTING = True
    SECRET_KEY = "test-secret"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_TRACK_MODIFICATIONS = False


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def signup(client, username="alex", password="password123"):
    return client.post("/api/signup", json={"username": username, "password": password})


@pytest.fixture
def auth_client(client):
    """A client that is already signed up and logged in as 'alex'."""
    assert signup(client).status_code == 201
    return client


@pytest.fixture
def other_client(app):
    """A second, separate browser logged in as 'blake'."""
    other = app.test_client()
    assert signup(other, "blake").status_code == 201
    return other


def make_drill(client, name="Partner Passing", **extra):
    body = {"name": name, "category": "Passing", "skill_level": "Beginner", "default_minutes": 12, **extra}
    response = client.post("/api/drills", json=body)
    assert response.status_code == 201, response.get_json()
    return response.get_json()["drill"]
