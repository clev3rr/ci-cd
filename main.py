from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI(title="Lab 1 API", description="REST API для лабораторної роботи 1")

# модель даних
class Item(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

items_db = []

@app.get("/api/items", response_model=List[Item])
def get_items():
    """Отримати список об'єктів"""
    return items_db

@app.get("/api/items/{item_id}", response_model=Item)
def get_item(item_id: int):
    """Отримати об'єкт за ідентифікатором"""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Об'єкт не знайдено")

@app.post("/api/items", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(item: Item):
    """Створити новий об'єкт"""
    # перевірка на унікальність ID
    if any(existing_item.id == item.id for existing_item in items_db):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Об'єкт з таким ID вже існує")
    items_db.append(item)
    return item

@app.put("/api/items/{item_id}", response_model=Item)
def update_item(item_id: int, updated_item: Item):
    """Оновити наявний об'єкт"""
    for index, item in enumerate(items_db):
        if item.id == item_id:
            items_db[index] = updated_item
            return updated_item
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Об'єкт не знайдено")

@app.delete("/api/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int):
    """Видалити об'єкт"""
    for index, item in enumerate(items_db):
        if item.id == item_id:
            items_db.pop(index)
            return
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Об'єкт не знайдено")