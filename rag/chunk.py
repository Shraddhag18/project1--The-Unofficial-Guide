"""Stage 2 — Chunking.

Splits a document into overlapping passages small enough for the embedding
model's window. We split on paragraph/sentence boundaries first and only fall
back to a hard character cut when a single block is itself too large, so chunks
stay semantically coherent instead of being sliced mid-sentence.
"""

import re
from dataclasses import dataclass

from .config import CHUNK_SIZE, CHUNK_OVERLAP
from .ingest import Document

# Split points, strongest first: blank lines (paragraphs), then newlines,
# then sentence enders. Keeps related text together when possible.
_SPLIT_PATTERN = re.compile(r"(\n\s*\n|\n|(?<=[.!?])\s+)")


@dataclass
class Chunk:
    chunk_id: str
    text: str
    metadata: dict


def _segments(text: str) -> list[str]:
    """Break text into the smallest natural units we'll recombine into chunks."""
    parts = [p for p in _SPLIT_PATTERN.split(text) if p and not p.isspace()]
    return [p.strip() for p in parts if p.strip()]


def chunk_text(text: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Greedily pack natural segments into ~`size`-char chunks with `overlap`."""
    segments = _segments(text)
    chunks: list[str] = []
    current = ""

    for seg in segments:
        # A single oversized segment can't fit — hard-split it on char count.
        if len(seg) > size:
            if current:
                chunks.append(current)
                current = ""
            for i in range(0, len(seg), size - overlap):
                chunks.append(seg[i:i + size])
            continue

        candidate = f"{current} {seg}".strip() if current else seg
        if len(candidate) <= size:
            current = candidate
        else:
            chunks.append(current)
            # Start the next chunk with the tail of this one for continuity.
            tail = current[-overlap:] if overlap else ""
            current = f"{tail} {seg}".strip()

    if current:
        chunks.append(current)
    return [c for c in chunks if c.strip()]


def chunk_documents(docs: list[Document]) -> list[Chunk]:
    """Chunk every document, carrying source metadata onto each chunk."""
    out: list[Chunk] = []
    for doc in docs:
        pieces = chunk_text(doc.text)
        for i, piece in enumerate(pieces):
            meta = dict(doc.metadata)
            meta["doc_id"] = doc.doc_id
            meta["chunk_index"] = i
            out.append(Chunk(chunk_id=f"{doc.doc_id}::{i}", text=piece, metadata=meta))
    return out


if __name__ == "__main__":
    from .ingest import load_documents

    docs = load_documents()
    chunks = chunk_documents(docs)
    print(f"{len(docs)} documents -> {len(chunks)} chunks")
    if chunks:
        lengths = [len(c.text) for c in chunks]
        print(f"chunk length: min={min(lengths)} max={max(lengths)} "
              f"avg={sum(lengths)//len(lengths)}")
