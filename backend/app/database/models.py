from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy.sql import func

from app.database.base import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, nullable=False)


class Document(Base):
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True)

    filename = Column(String, nullable=False)

    uploaded_by = Column(
        Integer,
        ForeignKey("users.id")
    )

    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )


class Product(Base):
    __tablename__ = "products"

    id = Column(Integer, primary_key=True)

    sku = Column(String)

    name = Column(String)

    category = Column(String)

    manufacturer = Column(String)


class Chunk(Base):
    __tablename__ = "chunks"

    id = Column(Integer, primary_key=True)

    document_id = Column(
        Integer,
        ForeignKey("documents.id")
    )

    product_id = Column(
        Integer,
        ForeignKey("products.id")
    )

    chunk_index = Column(Integer)

    text = Column(String)


class QueryLog(Base):
    __tablename__ = "query_logs"

    id = Column(Integer, primary_key=True)

    user_id = Column(
        Integer,
        ForeignKey("users.id")
    )

    query = Column(String)

    timestamp = Column(
        DateTime(timezone=True),
        server_default=func.now()
    )