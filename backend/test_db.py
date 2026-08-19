from app.database.qdrant import client


try:
    collections = client.get_collections()

    print("Qdrant connection successful!")
    print("\nCollections:")

    for collection in collections.collections:
        print("-", collection.name)

except Exception as e:
    print("Qdrant connection failed!")
    print(e)