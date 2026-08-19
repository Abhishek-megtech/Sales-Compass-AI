from app.ingestion.chunker import chunk_text


text = """
Product: Industrial Router

SKU: RT-1001

Manufacturer: Cisco

Category: Networking

Description: High-performance industrial router designed
for enterprise networking environments with advanced
security and routing capabilities.

Specifications:
Port Count: 24
Speed: 1 Gbps
Power: 220V
Warranty: 3 Years
"""


chunks = chunk_text(
    text,
    chunk_size=150,
    chunk_overlap=30,
)


print(f"Total chunks: {len(chunks)}")


for index, chunk in enumerate(chunks, start=1):

    print("\n" + "=" * 50)

    print(f"CHUNK {index}")

    print("=" * 50)

    print(chunk)