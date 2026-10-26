import pytest

from app.main import app


@pytest.fixture
def client():
    app.config["TESTING"] = True

    with app.test_client() as client:
        yield client


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert response.json["application"] == "ShopSphere"


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_ready(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json["status"] == "ready"


def test_books(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert len(response.json["books"]) == 3