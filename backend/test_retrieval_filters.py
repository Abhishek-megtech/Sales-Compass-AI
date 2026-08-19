from app.retrieval.retriever import retrieve


print("=" * 60)
print("SKU FILTER TEST")
print("=" * 60)


response = retrieve(
    query="Tell me about this product",
    top_k=5,
    sku="RT-1001",
)


print("\nQuery:")
print(response.query)

print("\nResults:")
print(response.total_results)


for index, result in enumerate(
    response.results,
    start=1,
):

    print("\n" + "-" * 50)

    print(f"RESULT {index}")

    print("Score:", result.score)

    print("Chunk ID:", result.chunk_id)

    print("Document ID:", result.document_id)

    print("Text:")
    print(result.text)

    print("Metadata:")
    print(result.metadata)