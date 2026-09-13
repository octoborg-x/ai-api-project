"""
Retrieval logic for finding relevant chunks in a vector store.
"""

import numpy as np

# pylint: disable=import-error
from vector_store import VectorStore


def cosine_similarity(v1, v2):
    """Compute cosine similarity between two numeric vectors."""
    v1 = np.array(v1)
    v2 = np.array(v2)
    if v1.shape != v2.shape:
        return 0.0
    dot = np.dot(v1, v2)
    norm1 = np.linalg.norm(v1)
    norm2 = np.linalg.norm(v2)
    if norm1 == 0 or norm2 == 0:
        return 0.0
    return dot / (norm1 * norm2)


class Retriever:
    """Handles querying the vector store for similar content."""

    # pylint: disable=too-few-public-methods
    def __init__(self, vector_store: VectorStore):
        self.vector_store = vector_store

    def search(self, query_embedding: list[float], top_k: int = 3):
        """Perform a similarity search against the vector store."""
        chunks = self.vector_store.get_all_chunks()
        scored_chunks = []
        for chunk in chunks:
            score = cosine_similarity(query_embedding, chunk.embedding)
            scored_chunks.append((score, chunk))

        # Sort by score descending
        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return scored_chunks[:top_k]
