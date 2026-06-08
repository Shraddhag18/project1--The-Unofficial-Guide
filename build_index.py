"""Build the vector index from everything in documents/.

    python build_index.py

Runs the first three pipeline stages end to end: ingest -> chunk -> embed+store.
Re-run it any time you add or change documents; it rebuilds from scratch.
"""

from rag.ingest import load_documents
from rag.chunk import chunk_documents
from rag.index import build_index
from rag.config import DOCUMENTS_DIR, CHROMA_DIR, COLLECTION_NAME


def main() -> None:
    print(f"Loading documents from {DOCUMENTS_DIR} ...")
    docs = load_documents()
    if not docs:
        print("No documents found. Add files to documents/ and re-run.")
        return
    print(f"  {len(docs)} documents loaded.")

    print("Chunking ...")
    chunks = chunk_documents(docs)
    lengths = [len(c.text) for c in chunks]
    print(f"  {len(chunks)} chunks "
          f"(avg {sum(lengths)//len(lengths)} chars, max {max(lengths)}).")

    print("Embedding + storing in ChromaDB (first run downloads the model) ...")
    collection = build_index(chunks)
    print(f"  Stored {collection.count()} vectors in "
          f"'{COLLECTION_NAME}' at {CHROMA_DIR}.")
    print("\nDone. Try:  python app.py")


if __name__ == "__main__":
    main()
