"""The Unofficial Guide — a local RAG pipeline over ASU campus-life documents.

Pipeline stages (one module each):
    ingest    -> load raw documents from documents/
    chunk     -> split documents into overlapping passages
    index     -> embed chunks (sentence-transformers) + store them (ChromaDB)
    retrieve  -> embed a query and pull the top-k most similar chunks
    generate  -> ask Groq's LLM to answer using ONLY the retrieved chunks
"""
