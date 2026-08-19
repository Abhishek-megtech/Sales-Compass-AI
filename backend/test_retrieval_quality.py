from app.retrieval.retriever import retrieve


print("=" * 60)
print("EMPTY RESULT TEST")
print("=" * 60)


response = retrieve(
    query="industrial router",
    top_k=5,
    score_threshold=0.5,
)


print("\nQuery:")
print(response.query)

print("\nTotal results:")
print(response.total_results)

print("\nResults:")
print(response.results)

print("\n" + "=" * 60)
print("TOP-K VALIDATION")
print("=" * 60)


try:

    retrieve(
        query="industrial router",
        top_k=0,
    )

except ValueError as e:

    print("Correctly rejected:", e)