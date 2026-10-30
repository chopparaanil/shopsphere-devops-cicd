import pytest

from app.main import app, db, Book


@pytest.fixture
def client(tmp_path):
    database_file = tmp_path / "test.db"

    app.config.update(
        TESTING=True,
        SQLALCHEMY_DATABASE_URI=f"sqlite:///{database_file}",
    )

    with app.app_context():
        db.drop_all()
        db.create_all()

    with app.test_client() as test_client:
        yield test_client

    with app.app_context():
        db.session.remove()
        db.drop_all()


def test_home(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"ShopSphere Book Store" in response.data


def test_health(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json["status"] == "healthy"


def test_ready(client):
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json["status"] == "ready"


def test_get_books_empty(client):
    response = client.get("/books")

    assert response.status_code == 200
    assert response.json["books"] == []


def test_add_and_get_book(client):
    response = client.post(
        "/books",
        json={"name": "AWS DevOps Guide", "price": 799},
    )

    assert response.status_code == 201
    assert response.json["book"]["name"] == "AWS DevOps Guide"

    response = client.get("/books")

    assert response.status_code == 200
    assert len(response.json["books"]) == 1
    assert response.json["books"][0]["price"] == 799.0


def test_reject_invalid_book(client):
    response = client.post(
        "/books",
        json={"name": "", "price": 799},
    )

    assert response.status_code == 400


def test_delete_book(client):
    create_response = client.post(
        "/books",
        json={"name": "Kubernetes Essentials", "price": 699},
    )

    book_id = create_response.json["book"]["id"]

    delete_response = client.delete(f"/books/{book_id}")

    assert delete_response.status_code == 200

    books_response = client.get("/books")

    assert books_response.json["books"] == []


def test_delete_missing_book(client):
    response = client.delete("/books/9999")

    assert response.status_code == 404