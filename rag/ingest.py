"""Stage 1 — Document ingestion.

Loads every file in documents/ into a uniform `Document` record. Each file may
carry a small YAML-style front-matter header recording where it came from:

    ---
    title: ASU Dining — Meal Plans
    source_url: https://sundevildining.asu.edu/meal-plans
    source_type: official
    ---
    <the actual text...>

Front matter is optional; files without it still load (metadata falls back to
the filename). Supported extensions: .md, .txt, and .pdf (via pdfplumber).
"""

from dataclasses import dataclass, field
from pathlib import Path

from .config import DOCUMENTS_DIR


@dataclass
class Document:
    doc_id: str                       # stable id (the filename stem)
    text: str
    metadata: dict = field(default_factory=dict)


def _parse_front_matter(raw: str) -> tuple[dict, str]:
    """Split optional `--- ... ---` front matter from the body.

    Intentionally tiny: we only support flat `key: value` pairs, which is all
    our document headers use. Avoids pulling in a YAML dependency.
    """
    if not raw.lstrip().startswith("---"):
        return {}, raw
    stripped = raw.lstrip()
    end = stripped.find("\n---", 3)
    if end == -1:
        return {}, raw
    header = stripped[3:end]
    body = stripped[end + 4:].lstrip("\n")
    meta: dict = {}
    for line in header.splitlines():
        if ":" in line:
            key, _, value = line.partition(":")
            meta[key.strip()] = value.strip()
    return meta, body


def _read_pdf(path: Path) -> str:
    import pdfplumber  # imported lazily so non-PDF corpora don't need it

    pages = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            pages.append(page.extract_text() or "")
    return "\n\n".join(pages)


def load_documents(documents_dir: Path = DOCUMENTS_DIR) -> list[Document]:
    """Return all documents found in `documents_dir`, sorted by filename."""
    docs: list[Document] = []
    for path in sorted(documents_dir.iterdir()):
        if path.name.startswith(".") or not path.is_file():
            continue

        if path.suffix.lower() in {".md", ".txt"}:
            meta, body = _parse_front_matter(path.read_text(encoding="utf-8"))
        elif path.suffix.lower() == ".pdf":
            meta, body = {}, _read_pdf(path)
        else:
            continue  # skip unknown file types

        body = body.strip()
        if not body:
            continue

        meta.setdefault("title", path.stem.replace("_", " "))
        meta.setdefault("source_url", "")
        meta.setdefault("source_type", "unknown")
        meta["filename"] = path.name

        docs.append(Document(doc_id=path.stem, text=body, metadata=meta))
    return docs


if __name__ == "__main__":
    loaded = load_documents()
    print(f"Loaded {len(loaded)} documents from {DOCUMENTS_DIR}")
    for d in loaded:
        print(f"  - {d.doc_id:35s} {len(d.text):>6d} chars  [{d.metadata['source_type']}]")
