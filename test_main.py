import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from database import engine, get_session
from main import app


@pytest.fixture
def client():
    with engine.connect() as connection:
        transaction = connection.begin()

        def get_test_session():
            with Session(
                bind=connection,
                expire_on_commit=False,
                join_transaction_mode="create_savepoint",
            ) as session:
                yield session

        app.dependency_overrides[get_session] = get_test_session
        try:
            with TestClient(app) as test_client:
                yield test_client
        finally:
            app.dependency_overrides.pop(get_session)
            transaction.rollback()


def test_create_item(client):
    response = client.post(
        "/api/items",
        json={"id": 1, "name": "Тестовий об'єкт", "description": "Опис"},
    )
    assert response.status_code == 201
    assert response.json()["name"] == "Тестовий об'єкт"


def test_get_items(client):
    response = client.post(
        "/api/items", json={"id": 1, "name": "Тестовий об'єкт"}
    )
    assert response.status_code == 201

    response = client.get("/api/items")
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_get_nonexistent_item(client):
    response = client.get("/api/items/999")
    assert response.status_code == 404