from app.database.qdrant import client
from qdrant_client.models import PayloadSchemaType


COLLECTION_NAME = "product_chunks_test"


def create_indexes():

    fields = {
        "sku": PayloadSchemaType.KEYWORD,
        "category": PayloadSchemaType.KEYWORD,
        "manufacturer": PayloadSchemaType.KEYWORD,
        "document_id": PayloadSchemaType.INTEGER,
    }

    for field_name, field_type in fields.items():

        client.create_payload_index(
            collection_name=COLLECTION_NAME,
            field_name=field_name,
            field_schema=field_type,
        )

        print(
            f"Created index: {field_name}"
        )


if __name__ == "__main__":
    create_indexes()