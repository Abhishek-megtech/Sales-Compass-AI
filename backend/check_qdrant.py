import os

from dotenv import load_dotenv
from app.database.qdrant import client

load_dotenv()

collection_name = os.getenv(
    "QDRANT_COLLECTION_NAME",
    "product_chunks"
)

info = client.get_collection(collection_name)

print("Collection:", collection_name)
print("Vector size:", info.config.params.vectors.size)
print("Distance:", info.config.params.vectors.distance)