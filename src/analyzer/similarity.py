"""Text similarity. TF-IDF baseline always works; embeddings are optional."""
from __future__ import annotations

from functools import lru_cache

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity


def tfidf_similarity(a: str, b: str) -> float:
    if not a.strip() or not b.strip():
        return 0.0
    vec = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
    m = vec.fit_transform([a, b])
    return float(cosine_similarity(m[0], m[1])[0, 0])


@lru_cache(maxsize=1)
def _load_model(name: str):
    from sentence_transformers import SentenceTransformer  # optional dependency

    return SentenceTransformer(name)


def embedding_similarity(a: str, b: str, model_name: str = "all-MiniLM-L6-v2") -> float:
    model = _load_model(model_name)
    ea, eb = model.encode([a, b], normalize_embeddings=True)
    return float(max(0.0, ea @ eb))


def text_similarity(a: str, b: str, method: str = "tfidf") -> float:
    if method == "embedding":
        return embedding_similarity(a, b)
    return tfidf_similarity(a, b)
