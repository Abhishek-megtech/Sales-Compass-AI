from app.database.qdrant import client
from app.retrieval.embedder import embedder

from qdrant_client.models import PointStruct
import uuid

COLLECTION_NAME = "product_chunks_test"


DUMMY_PRODUCTS = [
    {
        "chunk_id": "test-001",
        "document_id": 1,
        "text": (
            "SKU: RT-1001\n"
            "Product: Industrial Router\n"
            "Category: Networking\n"
            "Manufacturer: Cisco\n"
            "Description: High performance industrial "
            "router for enterprise networking."
        ),
        "metadata": {
            "sku": "RT-1001",
            "category": "Networking",
            "manufacturer": "Cisco",
            "filename": "test_catalog.pdf",
            "page_number": 1,
        },
    },
    {
        "chunk_id": "test-002",
        "document_id": 1,
        "text": (
            "SKU: SW-2001\n"
            "Product: Enterprise Network Switch\n"
            "Category: Networking\n"
            "Manufacturer: Cisco\n"
            "Description: Managed network switch "
            "with high speed Ethernet ports."
        ),
        "metadata": {
            "sku": "SW-2001",
            "category": "Networking",
            "manufacturer": "Cisco",
            "filename": "test_catalog.pdf",
            "page_number": 2,
        },
    },
    {
        "chunk_id": "test-003",
        "document_id": 2,
        "text": (
            "SKU: FW-3001\n"
            "Product: Enterprise Firewall\n"
            "Category: Security\n"
            "Manufacturer: Fortinet\n"
            "Description: Next generation firewall "
            "for enterprise security."
        ),
        "metadata": {
            "sku": "FW-3001",
            "category": "Security",
            "manufacturer": "Fortinet",
            "filename": "security_catalog.pdf",
            "page_number": 1,
        },
    },
    {
        "chunk_id": "test-004",
        "document_id": 2,
        "text": (
            "SKU: AP-4001\n"
            "Product: Wireless Access Point\n"
            "Category: Networking\n"
            "Manufacturer: Cisco\n"
            "Description: Enterprise wireless access "
            "point for office networks."
        ),
        "metadata": {
            "sku": "AP-4001",
            "category": "Networking",
            "manufacturer": "Cisco",
            "filename": "network_catalog.pdf",
            "page_number": 3,
        },
    },
]

def seed_data():

    points = []

    for product in DUMMY_PRODUCTS:

        vector = embedder.embed_query(
            product["text"]
        )

        points.append(
            PointStruct(
                id=str(uuid.uuid4()),
                vector=vector,
                payload={
                    "chunk_id": product["chunk_id"],
                    "document_id": product["document_id"],
                    "text": product["text"],
                    **product["metadata"],
                },
            )
        )

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points,
    )

    print(
        f"Inserted {len(points)} test points."
    )


if __name__ == "__main__":
    seed_data()

