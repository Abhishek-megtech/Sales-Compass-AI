from app.retrieval.embedder import embedder


query = "Tell me about industrial routers"


vector = embedder.embed_query(query)


print("Query:")
print(query)

print("\nVector dimension:")
print(len(vector))

print("\nFirst 10 values:")
print(vector[:10])