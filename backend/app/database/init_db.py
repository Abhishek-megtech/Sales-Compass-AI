from app.database.base import Base
from app.database.models import User, Document, Product, Chunk, QueryLog
from app.database.session import engine


def init_database():
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")


if __name__ == "__main__":
    init_database()