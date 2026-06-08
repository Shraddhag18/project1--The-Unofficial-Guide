"""Query interface for The Unofficial Guide.

    python app.py            # interactive command-line Q&A
    python app.py --web      # Gradio web UI (requires `pip install gradio`)
    python app.py "your question here"   # answer one question and exit

Generation needs a GROQ_API_KEY in .env. Run build_index.py first.
"""

import sys

from rag.generate import answer


def _format(result) -> str:
    out = [result.text]
    if result.sources:
        out.append("\nSources:")
        for i, s in enumerate(result.sources, start=1):
            title = s.metadata.get("title", s.metadata.get("doc_id"))
            url = s.metadata.get("source_url", "")
            out.append(f"  [{i}] {title} {url}".rstrip())
    return "\n".join(out)


def run_cli() -> None:
    print("The Unofficial Guide — ASU campus life. Ask a question (Ctrl-C to quit).\n")
    try:
        while True:
            q = input("you > ").strip()
            if not q:
                continue
            if q.lower() in {"exit", "quit"}:
                break
            print("\n" + _format(answer(q)) + "\n")
    except (KeyboardInterrupt, EOFError):
        print("\nBye!")


def run_web() -> None:
    import gradio as gr

    def respond(message, _history):
        return _format(answer(message))

    gr.ChatInterface(
        respond,
        title="The Unofficial Guide — ASU Campus Life",
        description="Answers are grounded in collected campus-life documents, with sources cited.",
    ).launch()


def main() -> None:
    args = sys.argv[1:]
    if args and args[0] == "--web":
        run_web()
    elif args:
        print(_format(answer(" ".join(args))))
    else:
        run_cli()


if __name__ == "__main__":
    main()
