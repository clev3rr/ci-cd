from fastapi.testclient import TestClient
from main import app, items_db

client = TestClient(app)

# очищення бази перед кожним тестом
def setup_function():
    items_db.clear()

def test_create_item():
    response = client.post("/api/items", json={"id": 1, "name": "Тестовий об'єкт", "description": "Опис"})
    assert response.status_code == 201
    assert response.json()["name"] == "Тестовий об'єкт"

def test_get_items():
    client.post("/api/items", json={"id": 1, "name": "Тестовий об'єкт"})
    response = client.get("/api/items")
    assert response.status_code == 200
    assert len(response.json()) == 1
    
def test_get_nonexistent_item():
    response = client.get("/api/items/999")
    assert response.status_code == 404