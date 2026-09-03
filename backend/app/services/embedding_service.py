import os
from typing import List
import numpy as np

# We defer importing SentenceTransformer to avoid slow startups unless needed
# but for the abstraction, we load it lazily or globally depending on the framework.

class EmbeddingService:
    """
    Abstract embedding service.
    Currently configured to use local sentence-transformers (all-MiniLM-L6-v2)
    for high reproducibility, zero cost, and strict privacy.
    """
    
    _model = None
    _dimension = None

    @classmethod
    def _initialize(cls):
        if cls._model is None:
            # Lazy load
            from sentence_transformers import SentenceTransformer
            # Using a very lightweight local embedding model
            cls._model = SentenceTransformer("all-MiniLM-L6-v2")
            # Dynamically detect dimension
            cls._dimension = cls._model.get_sentence_embedding_dimension()

    @classmethod
    def get_dimension(cls) -> int:
        cls._initialize()
        return cls._dimension

    @classmethod
    def get_embedding(cls, text: str) -> List[float]:
        """
        Returns a single vector for a text string.
        """
        cls._initialize()
        # Returns a numpy array, convert to list of floats for pgvector
        vector = cls._model.encode(text, convert_to_numpy=True)
        return vector.tolist()

    @classmethod
    def get_embeddings(cls, texts: List[str]) -> List[List[float]]:
        """
        Batch process multiple texts.
        """
        cls._initialize()
        vectors = cls._model.encode(texts, convert_to_numpy=True)
        return vectors.tolist()
