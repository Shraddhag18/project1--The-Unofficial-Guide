# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

I'm building an unofficial guide to **ASU campus life on the Tempe campus** —
the practical, day-to-day knowledge a student actually needs: parking permits
and which lots are cheapest, meal plans and how Maroon & Gold dollars work,
residence halls, getting around by shuttle and light rail, the rec center,
joining clubs, campus safety, the library, and surviving the Arizona heat.

This knowledge is valuable because it's scattered. Official ASU pages each cover
one narrow topic in isolation, the numbers change yearly, and the genuinely
useful framing ("Lot 59 is the cheapest," "arrive before 9 AM," "the MU has the
best shade") lives in student blogs and the campus newspaper, not the catalog. A
single grounded assistant that pulls across all of these is something no one
official page offers.

---

## Documents

I collected 10 sources spanning distinct subtopics, mixing official ASU pages
with unofficial student-facing sources, so retrieval has both authoritative
numbers and practical framing.

| #  | Source | Description | URL or location |
|----|--------|-------------|-----------------|
| 1  | ASU Parking & Transit Services | Tempe permit types, lot/garage prices | https://cfo.asu.edu/pts-parking-tempe |
| 2  | Live SoL ASU (unofficial) | Student-perspective parking tips & alternatives | https://livesolasu.com/blog/asu-parking-sol/ |
| 3  | Sun Devil Hospitality | Meal plans, M&G dollars, dining halls FAQ | https://sundevilhospitality.asu.edu/meal-plans/meal-plan-faq |
| 4  | ASU Housing | Hassayampa Academic Village residence hall | https://housing.asu.edu/.../hassayampa-academic-village |
| 5  | ASU Parking & Transit Services | Shuttles, light rail, U-Pass, ride home | https://cfo.asu.edu/transit |
| 6  | Sun Devil Fitness | SDFC Tempe amenities and access | https://fitness.asu.edu/facilities/amenities/tempe |
| 7  | EOSS (Student Orgs) | Joining clubs via Sun Devil Sync | https://eoss.asu.edu/clubs/join |
| 8  | ASU CFO / Student Life | LiveSafe app, Safety Escort, ASU PD | https://cfo.asu.edu/livesafe-mobile-app |
| 9  | ASU Library | Hayden Library floors, study rooms | https://lib.asu.edu/hayden/building |
| 10 | ASU Wellness / State Press | Surviving the Arizona heat on campus | https://wellness.asu.edu/blog/5-tips-surviving-arizona-summer |

The raw text for each is saved in `documents/` (numbered `.md` files) with
front matter recording the title, source URL, and whether the source is
official or unofficial.

---

## Chunking Strategy

**Chunk size:** ~900 characters (≈ 200–225 tokens).

**Overlap:** 150 characters.

**Reasoning:** The embedding model (all-MiniLM-L6-v2) silently truncates input
past 256 word-pieces, so a chunk much larger than ~1000 characters would lose
text at embed time. 900 characters keeps every chunk safely inside that window.
The documents are short, fact-dense reference pages (price lists, hours,
amenity bullets) rather than long narrative, so a moderate chunk keeps a
self-contained topic (e.g. one permit price table, one residence hall's
amenities) together. The 150-char overlap means a fact that lands on a chunk
boundary — like a price line right after a heading — is still recoverable from
the neighboring chunk. I split on paragraph/sentence boundaries first and only
hard-cut a single oversized block, so chunks stay coherent instead of being
sliced mid-sentence. Across the 10 documents this produced **27 chunks**
(avg 729 chars, max 897).

---

## Retrieval Approach

**Embedding model:** `all-MiniLM-L6-v2` via sentence-transformers — runs
locally, no API key or rate limits, 384-dimensional, fast, and strong on short
English passages. Embeddings are L2-normalized and stored in ChromaDB with
cosine distance.

**Top-k:** 4 chunks per query, with a relevance filter: any chunk whose cosine
distance exceeds 0.75 (similarity < 0.25) is dropped, so a question outside the
corpus can legitimately return nothing and let the model abstain.

**Production tradeoff reflection:** If cost weren't a constraint and this served
real students, I'd weigh a larger hosted embedding model (e.g. OpenAI
`text-embedding-3-large` or a Cohere multilingual model). The wins:
domain-specific accuracy (ASU jargon like "M&G," "SunCard," "FLASH," "Barrett"
that MiniLM may treat as low-signal tokens), a longer context window so I could
embed bigger chunks without truncation, and multilingual support for ASU's large
international population asking questions in their first language. The costs:
per-query API latency and dollar cost, an external dependency and rate limits,
and sending student queries off-device. For a small, English, fact-lookup corpus
like this one, local MiniLM is the right call; the hosted upgrade pays off mainly
at larger scale or with multilingual users.

---

## Evaluation Plan

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What is the cheapest student parking permit at Tempe and which lot is it for? | $280/year, Lot 59 (least expensive commuter option). |
| 2 | How often does the Tempe FLASH shuttle run and what hours? | Every 12–15 minutes, Mon–Fri 7 a.m.–10 p.m. (limited 7–6 on breaks). |
| 3 | How do Maroon & Gold (M&G) Dollars work and what's the minimum purchase? | Tax-free dollar-for-dollar balance on the ASU ID, usable at dining locations; $25 minimum; bonus tiers 5–20%. |
| 4 | When does the Safety Escort service run and how do I request one? | 7 p.m.–2 a.m., 7 days/week; request via the LiveSafe app or call 480-965-1515. |
| 5 | Who lives in Hassayampa Academic Village and what bed setup does it have? | W. P. Carey business students; double-occupancy suite-style rooms, Twin XL (36x80) with lofting available. |

These are specific enough to grade as right/wrong and each targets a different
document, so they also test whether retrieval routes to the correct source.

---

## Anticipated Challenges

1. **Stale or conflicting numbers across sources.** Prices and hours change
   yearly, and the official page and the unofficial student blog quote different
   parking ranges ($280–$950 official vs. "$210–$780" in the blog). Retrieval
   could surface the unofficial figure and present it as authoritative. Mitigation:
   keep source type in metadata and cite sources so a user can see which is which.

2. **Facts split across a chunk boundary.** A price or a phone number that lands
   right after a heading can end up in a different chunk than the context that
   makes it findable, so a query matches the heading chunk but misses the number.
   The 150-char overlap is meant to reduce this but won't eliminate it for long
   tables.

3. **Off-topic / out-of-corpus questions.** Someone may ask about tuition or a
   specific professor, which the corpus doesn't cover. Without a relevance floor
   the system would hand the LLM weakly-related chunks and invite a hallucinated
   answer. The distance filter + an explicit "I don't have enough information"
   instruction are the guard.

---

## Architecture

```
                  ASU campus-life web pages (official + unofficial)
                                   │
            ┌──────────────────────┴───────────────────────┐
            │ STAGE 1 — Ingestion        rag/ingest.py       │
            │ Load documents/*.md, parse source front matter │
            └──────────────────────┬───────────────────────┘
                                   │  Document(text, metadata)
            ┌──────────────────────┴───────────────────────┐
            │ STAGE 2 — Chunking         rag/chunk.py         │
            │ ~900-char chunks, 150 overlap, boundary-aware   │
            └──────────────────────┬───────────────────────┘
                                   │  Chunk[]  (27 chunks)
            ┌──────────────────────┴───────────────────────┐
            │ STAGE 3 — Embed + Store    rag/index.py         │
            │ all-MiniLM-L6-v2  →  ChromaDB (cosine, on disk) │
            └──────────────────────┬───────────────────────┘
                                   │  persistent vector store
            ┌──────────────────────┴───────────────────────┐
            │ STAGE 4 — Retrieval        rag/retrieve.py      │
            │ embed query → top-4, drop distance > 0.75       │
            └──────────────────────┬───────────────────────┘
                                   │  Retrieved[] (text + source)
            ┌──────────────────────┴───────────────────────┐
            │ STAGE 5 — Generation       rag/generate.py      │
            │ Groq llama-3.3-70b, grounded system prompt,     │
            │ numbered sources, cite-or-abstain               │
            └──────────────────────┬───────────────────────┘
                                   │
                    Interface — app.py (CLI / Gradio)
```

Entry points: `build_index.py` runs stages 1–3; `app.py` runs stages 4–5 per
query.

---

## AI Tool Plan

**Milestone 3 — Ingestion and chunking:** Use Claude (Claude Code). Give it the
Domain, Documents, and Chunking Strategy sections above and ask it to implement
`load_documents()` (with front-matter parsing for source metadata) and
`chunk_text()` with my 900-char / 150-overlap spec, splitting on natural
boundaries. Verify by running the chunker on the real corpus and checking the
reported chunk count, and that no chunk exceeds the embedding window.

**Milestone 4 — Embedding and retrieval:** Give Claude the Retrieval Approach
section and have it wire `all-MiniLM-L6-v2` to a persistent ChromaDB collection
with cosine distance, plus a `retrieve()` that embeds the query, returns top-4,
and applies the 0.75 distance filter. Verify with the eval questions by
inspecting whether the top chunks come from the expected document (e.g. the
parking question returns the "$280 / Lot 59" chunk).

**Milestone 5 — Generation and interface:** Give Claude the grounding goal and
have it write the Groq call with a system prompt that forbids outside knowledge,
requires bracketed source citations, and abstains when context is insufficient,
plus a CLI/Gradio interface. Verify by running the 5 eval questions end to end
and confirming answers cite sources and that an out-of-corpus question abstains.
