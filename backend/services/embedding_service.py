import re
from typing import List, Tuple
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from backend.utils.text_utils import clean_text, chunk_text

class EmbeddingService:
    """
    Local Vector Search and Retrieval engine for Document Q&A / RAG.
    Uses TF-IDF and Cosine Similarity for fast, deterministic, zero-latency retrieval
    without external heavy model overhead.
    """

    def __init__(self):
        pass

    def retrieve_relevant_chunks(
        self,
        query: str,
        document_chunks: List[str],
        top_k: int = 3,
        threshold: float = 0.05
    ) -> List[Tuple[str, float]]:
        """
        Calculates cosine similarity between user query and document chunks.
        Returns top-k most relevant text chunks along with their similarity scores.
        """
        if not document_chunks or not query.strip():
            return []

        # Clean chunks and query
        corpus = [clean_text(c) for c in document_chunks if c.strip()]
        if not corpus:
            return []

        clean_q = clean_text(query)

        try:
            vectorizer = TfidfVectorizer(
                stop_words='english',
                ngram_range=(1, 2),
                max_features=5000
            )
            tfidf_matrix = vectorizer.fit_transform(corpus)
            query_vector = vectorizer.transform([clean_q])

            similarities = cosine_similarity(query_vector, tfidf_matrix).flatten()
            
            # Rank indices by highest similarity
            ranked_indices = np.argsort(similarities)[::-1]

            results = []
            for idx in ranked_indices[:top_k]:
                score = float(similarities[idx])
                if score >= threshold:
                    results.append((corpus[idx], score))
                elif len(results) == 0:
                    # Provide top match if no items pass strict threshold
                    results.append((corpus[idx], score))

            return results
        except Exception:
            # Fallback keyword match if vectorizer encounters unigram edge case
            query_words = set(re.findall(r'\w+', clean_q.lower()))
            scored = []
            for chunk in corpus:
                chunk_words = set(re.findall(r'\w+', chunk.lower()))
                common = len(query_words.intersection(chunk_words))
                scored.append((chunk, float(common)))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]

embedding_service = EmbeddingService()
