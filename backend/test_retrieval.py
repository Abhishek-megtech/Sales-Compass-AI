from app.retrieval.retriever import retrieve


query = "wireless access point"


results = retrieve(
    query=query,
    top_k=2,
)


print("\n" + "=" * 60)
print("RETRIEVAL RESULTS")
print("=" * 60)

print("\nQuery:")
print(query)

print(f"\nResults returned: {len(results)}")


for index, result in enumerate(
    results,
    start=1,
):

    print("\n" + "-" * 60)

    print(f"RESULT {index}")

    print("-" * 60)

    print("Score:")
    print(result["score"])

    print("\nChunk ID:")
    print(result["chunk_id"])

    print("\nDocument ID:")
    print(result["document_id"])

    print("\nText:")
    print(result["text"])

    print("\nMetadata:")
    print(result["metadata"])