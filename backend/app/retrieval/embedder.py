import os

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer


load_dotenv()

MODEL_NAME = os.getenv(
    "EMBEDDING_MODEL",
    "BAAI/bge-small-en"
)


class QueryEmbedder:

    def __init__(self):
        print(
            f"Loading embedding model: {MODEL_NAME}"
        )

        self.model = SentenceTransformer(
            MODEL_NAME
        )

    def embed_query(self, query: str) -> list[float]:
        """
        Convert a user query into a vector.
        """

        if not query or not query.strip():
            raise ValueError(
                "Query cannot be empty."
            )

        vector = self.model.encode(
            query,
            normalize_embeddings=True
        )

        return vector.tolist()


embedder = QueryEmbedder()