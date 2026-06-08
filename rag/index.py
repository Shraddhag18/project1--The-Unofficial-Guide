"""Stage 3 — Embedding + vector store.

Embeds each chunk with sentence-transformers (all-MiniLM-L6-v2, local) and
persists them in a ChromaDB collection on disk. The same embedding function is
reused at query time by retrieve.py so query and document vectors live in the
same space.
"""

from functools import lru_cache

import chromadb
from sentence_transformers import SentenceTransformer

from .config import CHROMA_DIR, COLLECTION_NAME, EMBED_MODEL
from .chunk import Chunk


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    """Load the embedding model once and reuse it (it's a few hundred MB)."""
    return SentenceTransformer(EMBED_MODEL)


def embed(texts: list[str]) -> list[list[float]]:
    model = get_embedder()
    # normalize_embeddings=True -> vectors are unit length, so cosine distance
    # behaves sensibly and is comparable across queries.
    return model.encode(texts, normalize_embeddings=True, show_progress_bar=False).tolist()


@lru_cache(maxsize=1)
def get_client() -> chromadb.ClientAPI:
    CHROMA_DIR.mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=str(CHROMA_DIR))


def get_collection() -> chromadb.Collection:
    # cosine space matches our normalized embeddings.
    return get_client().get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )


def build_index(chunks: list[Chunk]) -> chromadb.Collection:
    """Embed `chunks` and (re)build the collection from scratch."""
    client = get_client()
    # Drop any existing collection so re-indexing is idempotent.
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME, metadata={"hnsw:space": "cosine"}
    )

    embeddings = embed([c.text for c in chunks])
    collection.add(
        ids=[c.chunk_id for c in chunks],
        embeddings=embeddings,
        documents=[c.text for c in chunks],
        metadatas=[c.metadata for c in chunks],
    )
    return collection
