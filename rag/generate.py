"""Stage 5 — Grounded generation.

Builds a prompt that hands the LLM ONLY the retrieved chunks and instructs it to
answer strictly from them, cite the sources it used by number, and say it can't
answer when the context doesn't cover the question. Grounding is enforced two
ways: (1) the system prompt's explicit rules, and (2) structurally — the model
literally never receives any campus knowledge except the numbered chunks below.
"""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from .config import GROQ_MODEL, GROQ_TEMPERATURE
from .retrieve import retrieve, Retrieved

load_dotenv()

SYSTEM_PROMPT = """\
You are "The Unofficial Guide," a question-answering assistant about ASU \
(Arizona State University) campus life. You answer ONLY using the numbered \
SOURCES provided in the user's message.

Rules:
1. Use only facts stated in the SOURCES. Do not add outside knowledge, even if \
you think you know the answer.
2. After each claim, cite the source(s) it came from using bracketed numbers, \
e.g. "Shuttles run every 10-15 minutes [2]."
3. If the SOURCES do not contain enough information to answer, say exactly: \
"I don't have enough information in my sources to answer that." Do not guess.
4. Keep answers concise and specific. Prefer the wording of the sources over \
paraphrase when a detail matters (times, prices, names, locations).
"""


@dataclass
class Answer:
    text: str
    sources: list[Retrieved]


def _format_context(hits: list[Retrieved]) -> str:
    blocks = []
    for i, h in enumerate(hits, start=1):
        title = h.metadata.get("title", h.metadata.get("doc_id", "source"))
        url = h.metadata.get("source_url", "")
        header = f"[{i}] {title}" + (f" ({url})" if url else "")
        blocks.append(f"{header}\n{h.text}")
    return "\n\n".join(blocks)


def _client():
    from groq import Groq

    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "GROQ_API_KEY is not set. Copy .env.example to .env and add your key."
        )
    return Groq()


def answer(query: str) -> Answer:
    hits = retrieve(query)
    if not hits:
        return Answer(
            text="I don't have enough information in my sources to answer that.",
            sources=[],
        )

    user_msg = (
        f"SOURCES:\n{_format_context(hits)}\n\n"
        f"QUESTION: {query}\n\n"
        "Answer using only the sources above, citing them by number."
    )

    completion = _client().chat.completions.create(
        model=GROQ_MODEL,
        temperature=GROQ_TEMPERATURE,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_msg},
        ],
    )
    return Answer(text=completion.choices[0].message.content.strip(), sources=hits)


if __name__ == "__main__":
    import sys

    q = " ".join(sys.argv[1:]) or "How often do the intercampus shuttles run?"
    result = answer(q)
    print(result.text)
    if result.sources:
        print("\nSources:")
        for i, s in enumerate(result.sources, start=1):
            title = s.metadata.get("title", s.metadata.get("doc_id"))
            url = s.metadata.get("source_url", "")
            print(f"  [{i}] {title} {url}".rstrip())
