"""Central configuration for the pipeline.

Keeping every tunable knob in one place means the planning.md spec and the
running code can't drift apart — if a number changes here, change it in the
writeup too (chunk size, overlap, top-k, model names).
"""

from pathlib import Path

# --- Paths -------------------------------------------------------------------
ROOT = Path(__file__).resolve().parent.parent
DOCUMENTS_DIR = ROOT / "documents"
CHROMA_DIR = ROOT / "chroma_db"          # gitignored local vector store
COLLECTION_NAME = "asu_campus_life"

# --- Chunking ----------------------------------------------------------------
# all-MiniLM-L6-v2 truncates input at 256 word-pieces (~1000 chars). We keep
# chunks comfortably under that so no text is silently dropped at embed time.
# ~900 chars ≈ 200-225 tokens. 150-char overlap keeps a sentence that straddles
# a boundary recoverable from at least one chunk.
CHUNK_SIZE = 900          # characters
CHUNK_OVERLAP = 150       # characters

# --- Embeddings --------------------------------------------------------------
EMBED_MODEL = "all-MiniLM-L6-v2"   # local, no API key, 384-dim

# --- Retrieval ---------------------------------------------------------------
TOP_K = 4                 # chunks pulled per query
# Cosine distance above this is treated as "not relevant enough" and dropped.
# Chroma returns distance = 1 - cosine_similarity, so smaller = more similar.
MAX_DISTANCE = 0.75

# --- Generation --------------------------------------------------------------
GROQ_MODEL = "llama-3.3-70b-versatile"
GROQ_TEMPERATURE = 0.2    # low: we want grounded recall, not creativity
