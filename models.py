from sqlalchemy import BigInteger
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class ItemRecord(Base):
    __tablename__ = "items"

    id: Mapped[int] = mapped_column(
        BigInteger, primary_key=True, autoincrement=False
    )
    name: Mapped[str]
    description: Mapped[str | None]