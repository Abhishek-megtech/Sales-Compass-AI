from app.database.qdrant import client
from qdrant_client.models import Distance, VectorParams


COLLECTION_NAME = "product_chunks_test"


def create_test_collection():

    existing = [
        collection.name
        for collection in client.get_collections().collections
    ]

    if COLLECTION_NAME in existing:

        print(
            f"Collection '{COLLECTION_NAME}' already exists."
        )

        return

    client.create_collection(
        collection_name=COLLECTION_NAME,
        vectors_config=VectorParams(
            size=384,
            distance=Distance.COSINE,
        ),
    )

    print(
        f"Created '{COLLECTION_NAME}'."
    )


if __name__ == "__main__":
    create_test_collection()