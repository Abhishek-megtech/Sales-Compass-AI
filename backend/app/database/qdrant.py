import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION_NAME = os.getenv(
    "QDRANT_COLLECTION_NAME",
    "product_chunks"
)

if not QDRANT_URL:
    raise ValueError("QDRANT_URL is not set in .env")

if not QDRANT_API_KEY:
    raise ValueError("QDRANT_API_KEY is not set in .env")


client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)


def create_collection():
    collections = client.get_collections().collections

    existing_collections = [
        collection.name
        for collection in collections
    ]

    if QDRANT_COLLECTION_NAME in existing_collections:
        print(
            f"Collection '{QDRANT_COLLECTION_NAME}' already exists."
        )
        return

    client.create_collection(
        collection_name=QDRANT_COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE
        )
    )

    print(
        f"Collection '{QDRANT_COLLECTION_NAME}' created successfully."
    )