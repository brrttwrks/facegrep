from __future__ import annotations

from settings import FACEGREP_POSTGRES_URI
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import relationship
from sqlalchemy import Column
from sqlalchemy import Table
from sqlalchemy import ForeignKey
from sqlalchemy.types import Text
from pgvector.sqlalchemy import Vector
from sqlalchemy import text
from typing import Optional

class Base(DeclarativeBase):
    pass


file_tag_assoc_table = Table(
    "files_tags",
    Base.metadata,
    Column(
        "file_id",
        ForeignKey("files.id"),
        primary_key=True
    ),
    Column(
        "filetag_id",
        ForeignKey("filetags.id"),
        primary_key=True
    ),
)


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(primary_key=True)
    hash = Column("hash", Text)
    filetags: Mapped[list["FileTag"]] = relationship(
        secondary=file_tag_assoc_table,
        back_populates = "files",
    )
    embeddings: Mapped[list["Embedding"]] = relationship()


class FileTag(Base):
    __tablename__ = "filetags"

    id: Mapped[int] = mapped_column(primary_key=True)
    source =  Column("source", Text)
    files: Mapped[list[File]] = relationship(
        secondary=file_tag_assoc_table,
        back_populates = "filetags",
    )


class Embedding(Base):
    __tablename__ = "embeddings"

    id: Mapped[int] = mapped_column(primary_key=True)
    embedding = Column(Vector(4096))
    file_path = Column(Text)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"))
    file: Mapped["File"] = relationship(back_populates="embeddings")
    person_id: Mapped[Optional[int]] = mapped_column(ForeignKey("persons.id"))
    person: Mapped[Optional["Person"]] = relationship(back_populates="embeddings")


class Person(Base):
    __tablename__ = "persons"

    id: Mapped[int] = mapped_column(primary_key=True)
    name = Column("name", Text)
    embeddings: Mapped[list["Embedding"]] = relationship(back_populates="person")


if __name__ == "__main__":
    engine = create_engine(FACEGREP_POSTGRES_URI, echo=True)
    with engine.connect() as conn:
        sql = "CREATE EXTENSION IF NOT EXISTS vector;"
        conn.execute(text(sql))
    Base.metadata.create_all(engine)
