"""
Unit tests — embedding_service.py

Tests:
1. Model loads without error
2. generate_embedding returns a list
3. Vector dimension is exactly 384 (BAAI/bge-small-en)
4. Empty text raises ValueError
5. Whitespace-only text raises ValueError
6. Non-string input raises ValueError
7. Two calls on the same text return identical vectors (determinism)
8. get_embedding_dimension returns 384
"""

import pytest
from app.knowledge_indexing.embedding_service import (
    generate_embedding,
    get_embedding_dimension,
    EXPECTED_EMBEDDING_DIM,
)


class TestGenerateEmbedding:
    def test_returns_list(self):
        result = generate_embedding("Industrial floor scrubber-dryer.")
        assert isinstance(result, list)

    def test_correct_dimension(self):
        result = generate_embedding("High-performance vacuum cleaner for workshops.")
        assert len(result) == EXPECTED_EMBEDDING_DIM, (
            f"Expected {EXPECTED_EMBEDDING_DIM} dimensions, got {len(result)}"
        )

    def test_values_are_floats(self):
        result = generate_embedding("Walk-behind cleaning machine.")
        assert all(isinstance(v, float) for v in result)

    def test_empty_string_raises(self):
        with pytest.raises(ValueError, match="empty"):
            generate_embedding("")

    def test_whitespace_only_raises(self):
        with pytest.raises(ValueError, match="empty"):
            generate_embedding("   \t\n  ")

    def test_non_string_raises(self):
        with pytest.raises(ValueError):
            generate_embedding(None)  # type: ignore

    def test_non_string_int_raises(self):
        with pytest.raises(ValueError):
            generate_embedding(123)  # type: ignore

    def test_deterministic_output(self):
        text = "Product SKU BD-4340 is a walk-behind scrubber."
        vec1 = generate_embedding(text)
        vec2 = generate_embedding(text)
        assert vec1 == vec2, "Same text should always produce the same embedding."

    def test_different_texts_differ(self):
        vec1 = generate_embedding("Karcher floor cleaning equipment.")
        vec2 = generate_embedding("Block jointing mortar for construction.")
        assert vec1 != vec2, "Different texts should produce different embeddings."

    def test_long_text(self):
        long_text = "word " * 500
        result = generate_embedding(long_text)
        assert len(result) == EXPECTED_EMBEDDING_DIM


class TestGetEmbeddingDimension:
    def test_returns_integer(self):
        dim = get_embedding_dimension()
        assert isinstance(dim, int)

    def test_returns_384(self):
        dim = get_embedding_dimension()
        assert dim == EXPECTED_EMBEDDING_DIM, (
            f"BAAI/bge-small-en should have dimension 384, got {dim}"
        )
