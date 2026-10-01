import math
import re
from collections import Counter
from typing import List, Tuple
from backend.utils.text_utils import clean_text

# Common English stop words
STOP_WORDS = {
    "a", "about", "above", "after", "again", "against", "all", "am", "an", "and", "any", "are", 
    "aren't", "as", "at", "be", "because", "been", "before", "being", "below", "between", "both", 
    "but", "by", "can't", "cannot", "could", "couldn't", "did", "didn't", "do", "does", "doesn't", 
    "doing", "don't", "down", "during", "each", "few", "for", "from", "further", "had", "hadn't", 
    "has", "hasn't", "have", "haven't", "having", "he", "he'd", "he'll", "he's", "her", "here", 
    "here's", "hers", "herself", "him", "himself", "his", "how", "how's", "i", "i'd", "i'll", 
    "i'm", "i've", "if", "in", "into", "is", "isn't", "it", "it's", "its", "itself", "let's", 
    "me", "more", "most", "mustn't", "my", "myself", "no", "nor", "not", "of", "off", "on", 
    "once", "only", "or", "other", "ought", "our", "ours", "ourselves", "out", "over", "own", 
    "same", "shan't", "she", "she'd", "she'll", "she's", "should", "shouldn't", "so", "some", 
    "such", "than", "that", "that's", "the", "their", "theirs", "them", "themselves", "then", 
    "there", "there's", "these", "they", "they'd", "they'll", "they're", "they've", "this", 
    "those", "through", "to", "too", "under", "until", "up", "very", "was", "wasn't", "we", 
    "we'd", "we'll", "we're", "we've", "were", "weren't", "what", "what's", "when", "when's", 
    "where", "where's", "which", "while", "who", "who's", "whom", "why", "why's", "with", 
    "won't", "would", "wouldn't", "you", "you'd", "you'll", "you're", "you've", "your", 
    "yours", "yourself", "yourselves"
}

class EmbeddingService:
    """
    Local Vector Search and Retrieval engine for Document Q&A / RAG.
    Uses pure-Python TF-IDF and Cosine Similarity for fast, deterministic, zero-latency retrieval
    without external heavy model or native DLL overhead.
    """

    def __init__(self):
        pass

    def _extract_ngrams(self, text: str) -> List[str]:
        """Extract unigrams (excluding stop words) and bigrams from text."""
        tokens = re.findall(r'\b[a-zA-Z0-9_]+\b', text.lower())
        unigrams = [w for w in tokens if w not in STOP_WORDS and len(w) > 1]
        bigrams = [f"{tokens[i]} {tokens[i+1]}" for i in range(len(tokens) - 1)]
        return unigrams + bigrams

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
            # 1. Tokenize corpus
            doc_ngrams_list = [self._extract_ngrams(doc) for doc in corpus]
            n_docs = len(corpus)

            # 2. Document frequencies
            df = Counter()
            for doc_ngrams in doc_ngrams_list:
                for term in set(doc_ngrams):
                    df[term] += 1

            # 3. Smoothed IDF: ln((1 + N) / (1 + df)) + 1
            idf = {term: math.log((1 + n_docs) / (1 + freq)) + 1.0 for term, freq in df.items()}

            # 4. Document TF-IDF unit vectors
            doc_vectors = []
            for doc_ngrams in doc_ngrams_list:
                counts = Counter(doc_ngrams)
                vec = {}
                norm_sq = 0.0
                for term, cnt in counts.items():
                    val = cnt * idf.get(term, 1.0)
                    vec[term] = val
                    norm_sq += val * val
                norm = math.sqrt(norm_sq)
                if norm > 0:
                    vec = {k: v / norm for k, v in vec.items()}
                doc_vectors.append(vec)

            # 5. Query TF-IDF unit vector
            q_ngrams = self._extract_ngrams(clean_q)
            q_counts = Counter(q_ngrams)
            q_vec = {}
            q_norm_sq = 0.0
            for term, cnt in q_counts.items():
                if term in idf:
                    val = cnt * idf[term]
                    q_vec[term] = val
                    q_norm_sq += val * val
            q_norm = math.sqrt(q_norm_sq)
            if q_norm > 0:
                q_vec = {k: v / q_norm for k, v in q_vec.items()}

            # 6. Cosine similarity: dot product of normalized vectors
            similarities = []
            for doc_vec in doc_vectors:
                sim = sum(q_weight * doc_vec.get(term, 0.0) for term, q_weight in q_vec.items())
                similarities.append(float(sim))

            # Rank indices by highest similarity
            ranked_indices = sorted(range(len(similarities)), key=lambda i: similarities[i], reverse=True)

            results = []
            for idx in ranked_indices[:top_k]:
                score = similarities[idx]
                if score >= threshold:
                    results.append((corpus[idx], score))
                elif len(results) == 0:
                    # Provide top match if no items pass strict threshold
                    results.append((corpus[idx], score))

            return results
        except Exception:
            # Fallback keyword match if edge case occurs
            query_words = set(re.findall(r'\w+', clean_q.lower()))
            scored = []
            for chunk in corpus:
                chunk_words = set(re.findall(r'\w+', chunk.lower()))
                common = len(query_words.intersection(chunk_words))
                scored.append((chunk, float(common)))
            scored.sort(key=lambda x: x[1], reverse=True)
            return scored[:top_k]

embedding_service = EmbeddingService()
