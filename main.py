from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from psycopg.errors import UniqueViolation
from pydantic import BaseModel, ConfigDict
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from database import get_session
from models import ItemRecord


app = FastAPI(title="Lab 4 API", description="REST API для роботи з об’єктами")
DatabaseSession = Annotated[Session, Depends(get_session)]


class Item(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    description: str | None = None


def find_item(session: Session, item_id: int) -> ItemRecord:
    record = session.get(ItemRecord, item_id)
    if record is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Об'єкт не знайдено",
        )
    return record


def save_changes(session: Session) -> None:
    try:
        session.commit()
    except IntegrityError as error:
        session.rollback()
        if isinstance(error.orig, UniqueViolation):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Об'єкт з таким ID вже існує",
            ) from error
        raise


@app.get("/api/items", response_model=list[Item])
def get_items(session: DatabaseSession):
    return session.scalars(select(ItemRecord).order_by(ItemRecord.id)).all()


@app.get("/api/items/{item_id}", response_model=Item)
def get_item(item_id: int, session: DatabaseSession):
    return find_item(session, item_id)


@app.post("/api/items", response_model=Item, status_code=status.HTTP_201_CREATED)
def create_item(item: Item, session: DatabaseSession):
    record = ItemRecord(**item.model_dump())
    session.add(record)
    save_changes(session)
    return record


@app.put("/api/items/{item_id}", response_model=Item)
def update_item(item_id: int, updated_item: Item, session: DatabaseSession):
    record = find_item(session, item_id)
    record.id = updated_item.id
    record.name = updated_item.name
    record.description = updated_item.description
    save_changes(session)
    return record


@app.delete("/api/items/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(item_id: int, session: DatabaseSession):
    record = find_item(session, item_id)
    session.delete(record)
    session.commit()