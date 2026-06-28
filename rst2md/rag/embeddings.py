"""Vector embedding generation using model2vec."""

from typing import List

from model2vec import StaticModel

MODEL_NAME = "minishlab/potion-base-8M"
_MODEL = None


def get_embedding_model():
    global _MODEL
    if _MODEL is None:
        _MODEL = StaticModel.from_pretrained(MODEL_NAME)
    return _MODEL


def reset_embedding_model_cache() -> None:
    global _MODEL
    _MODEL = None


def generate_embeddings(texts: List[str], batch_size: int = 1000) -> List[List[float]]:
    """Generate embeddings for a list of texts using model2vec."""
    model = get_embedding_model()
    embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch)
        embeddings.extend(batch_embeddings.tolist())
        if (i // batch_size) % 5 == 0:
            print(f"Generating embeddings... ({i + len(batch)}/{len(texts)})")
    return embeddings
