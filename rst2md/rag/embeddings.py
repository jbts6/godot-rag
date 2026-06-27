"""Vector embedding generation using model2vec."""

from typing import List


def generate_embeddings(texts: List[str], batch_size: int = 1000) -> List[List[float]]:
    """Generate embeddings for a list of texts using model2vec.

    Args:
        texts: List of text strings to embed.
        batch_size: Number of texts to process per batch.

    Returns:
        List of embedding vectors, one per input text.
    """
    from model2vec import StaticModel

    model = StaticModel.from_pretrained("minishlab/potion-base-8M")
    embeddings = []

    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        batch_embeddings = model.encode(batch)
        embeddings.extend(batch_embeddings.tolist())

        if (i // batch_size) % 5 == 0:
            print(f"Generating embeddings... ({i + len(batch)}/{len(texts)})")

    return embeddings
