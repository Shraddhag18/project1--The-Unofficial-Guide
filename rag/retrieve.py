"""Stage 4 — Retrieval.

Embeds the user's query with the same model used for indexing, then asks Chroma
for the top-k nearest chunks. Results beyond MAX_DISTANCE are filtered out so we
don't feed the LLM weakly-related text just to hit a fixed k — an empty result
here is what lets generation honestly say "I don't know."
"""

from dataclasses import dataclass

from .config import TOP_K, MAX_DISTANCE
from .index import embed, get_collection


@dataclass
class Retrieved:
    text: str
    metadata: dict
    distance: float       # cosine distance; lower = more similar

    @property
    def similarity(self) -> float:
        return 1.0 - self.distance


def retrieve(query: str, k: int = TOP_K, max_distance: float = MAX_DISTANCE) -> list[Retrieved]:
    collection = get_collection()
    if collection.count() == 0:
        raise RuntimeError(
            "The vector store is empty. Run `python build_index.py` first."
        )

    query_embedding = embed([query])[0]
    res = collection.query(
        query_embeddings=[query_embedding],
        n_results=k,
        include=["documents", "metadatas", "distances"],
    )

    hits: list[Retrieved] = []
    for text, meta, dist in zip(
        res["documents"][0], res["metadatas"][0], res["distances"][0]
    ):
        if dist <= max_distance:
            hits.append(Retrieved(text=text, metadata=meta, distance=dist))
    return hits


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "Where can I park on the Tempe campus?"
    print(f"Query: {q}\n")
    for r in retrieve(q):
        title = r.metadata.get("title", r.metadata.get("doc_id"))
        print(f"[sim={r.similarity:.3f}] {title}")
        print(f"    {r.text[:160]}...\n")
