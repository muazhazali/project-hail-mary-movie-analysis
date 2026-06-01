from functools import lru_cache

from sentence_transformers import SentenceTransformer


@lru_cache()
def _get_model(model_name: str = "all-MiniLM-L6-v2") -> SentenceTransformer:
    return SentenceTransformer(model_name)


def embed_texts(texts: list[str], model_name: str = "all-MiniLM-L6-v2") -> list[list[float]]:
    model = _get_model(model_name)
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    return [emb.tolist() for emb in embeddings]


def embed_query(text: str, model_name: str = "all-MiniLM-L6-v2") -> list[float]:
    model = _get_model(model_name)
    emb = model.encode(text, convert_to_numpy=True, show_progress_bar=False)
    return emb.tolist()

