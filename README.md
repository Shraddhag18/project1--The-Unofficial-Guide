# The Unofficial Guide — ASU Campus Life (Project 1)

A retrieval-augmented question-answering system over campus-life documents for
ASU's Tempe campus. Ask a practical question ("cheapest parking permit?", "how
do M&G Dollars work?") and get an answer grounded **only** in a small corpus of
collected official and unofficial sources, with the source documents cited.

---

## Domain

This system covers **day-to-day student life on ASU's Tempe campus** — parking
permits and which lot is cheapest, dining meal plans and how Maroon & Gold
dollars work, residence halls, getting around by shuttle and light rail, the
rec center, joining clubs, campus safety, the library, and surviving the Arizona
heat.

This knowledge is valuable because it's **scattered and changes yearly**. Each
official ASU page covers one narrow topic in isolation, the numbers (prices,
hours) are revised every year, and the genuinely useful framing ("Lot 59 is the
cheapest," "arrive before 9 AM," garages "have shade but cost more") lives in
student blogs and the campus newspaper, not the official catalog. A single
grounded assistant that pulls across all of these — and cites which source a
fact came from so you can tell the official figure from the student rumor — is
something no one official page offers.

---

## Document Sources

10 sources spanning distinct subtopics, deliberately mixing **official ASU
pages** (authoritative numbers) with **unofficial student-facing sources**
(practical framing). Each file in `documents/` carries front matter recording
its title, source URL, and whether it is official or unofficial.

| # | Source | Type | URL |
|---|--------|------|-----|
| 1 | ASU Parking & Transit Services — Tempe permits/lots/prices | official | https://cfo.asu.edu/pts-parking-tempe |
| 2 | Live SoL ASU — student parking tips & alternatives | unofficial | https://livesolasu.com/blog/asu-parking-sol/ |
| 3 | Sun Devil Hospitality — meal plans, M&G dollars FAQ | official | https://sundevilhospitality.asu.edu/meal-plans/meal-plan-faq |
| 4 | ASU Housing — Hassayampa Academic Village | official | https://housing.asu.edu/housing-communities/residential-colleges/hassayampa-academic-village |
| 5 | ASU Parking & Transit — shuttles, light rail, U-Pass | official | https://cfo.asu.edu/transit |
| 6 | Sun Devil Fitness — SDFC Tempe amenities & access | official | https://fitness.asu.edu/facilities/amenities/tempe |
| 7 | EOSS — joining clubs via Sun Devil Sync | official | https://eoss.asu.edu/clubs/join |
| 8 | ASU CFO / Student Life — LiveSafe app, Safety Escort, PD | official | https://cfo.asu.edu/livesafe-mobile-app |
| 9 | ASU Library — Hayden Library floors, study rooms | official | https://lib.asu.edu/hayden/building |
| 10 | ASU Wellness / State Press — surviving the Arizona heat | unofficial | https://wellness.asu.edu/blog/5-tips-surviving-arizona-summer |

---

## Chunking Strategy

**Chunk size:** ~600 characters (≈ 130–150 tokens) as a **ceiling**, not a fixed
length. Chunks are not padded to exactly 600 — see "Why the sizes vary" below.

**Overlap:** 120 characters.

**Why these choices fit my documents:** The embedding model
(`all-MiniLM-L6-v2`) silently truncates input past 256 word-pieces (~1000
chars), so chunks must stay well under that — 600 is comfortably safe. My
documents are **short, fact-dense reference pages** (price lists, hours, amenity
bullets), not long narrative, so each chunk should hold one self-contained topic
(one permit price table, one residence hall's room setup). I split on
paragraph/sentence boundaries first and only hard-cut a single oversized block,
so chunks stay coherent instead of being sliced mid-sentence. The 120-char
overlap keeps a fact that lands on a boundary — like a price right after a
heading — recoverable from the neighboring chunk.

**How I arrived at 600 (not just guessed):** I originally specced 900/150 (27
chunks). Retrieval testing showed that was slightly too large: several documents
bundle multiple subtopics into one chunk (the transit page mixes Valley Metro +
FLASH + intercampus shuttle; the dining page bundles the M&G explanation with
other FAQ items), which diluted the embedding. Two eval queries — the FLASH
shuttle and M&G Dollars — came back with a **top-result cosine distance of 0.50
and 0.52**, above the 0.5 "strong match" line. Re-chunking at 600/120 dropped
every query's top distance below 0.5 (FLASH 0.50→0.41, M&G 0.54→0.32) while
keeping all five answers accurate. Going smaller still (350) pushed two queries
back over 0.5 (lost context), so ~600 is the sweet spot for this corpus.

**Why the sizes vary (and why that's expected):** because the splitter packs
whole sentences/paragraphs up to the 600-char ceiling and stops at the last
boundary that fits, chunks land in a band (most are **530–598 chars**) rather
than all being identical — it never slices mid-sentence to hit a round number.
The smaller chunks are **document "tails":** the leftover text at the end of a
document after the full chunks are packed (e.g. a ~1,800-char page → three ~590
chunks + one ~230 remainder). Every chunk under ~350 chars is the last chunk of
its document. This variation is the cost of keeping chunks semantically intact,
which is exactly what makes them self-contained and readable; a fixed-length
cutter would give uniform sizes only by chopping words and sentences in half.

**Final chunk count:** **40 chunks** across 10 documents — sizes range from 215
to 598 chars (avg 518). The 215–350 char chunks are all document tails, as
described above.

### Sample chunks (5, each labeled with its source document)

**Chunk #0 — source: `01_parking_official.md` (590 chars)**
> # ASU Tempe Campus Parking (Parking & Transit Services) Three permit categories are available: automobile, motorcycle, and sustainable (HOV) options. Permits are purchased through the transportation portal at asu.aimsparking.com. ... ## Commuter automobile permit prices (per year) - Apache Boulevard, Rural Road, Tyler Street: $950 - Lot 32: $820

**Chunk #6 — source: `02_parking_student_guide.md` (585 chars)**
> from about $210 to $780 per academic year depending on the zone — always re-check current rates each year on ASU's site. ## Timing is everything Plan to arrive before 9:00 AM for the best chance at an open spot. ... ## Skip parking entirely - Valley Metro light rail and buses reach campus and downtown Tempe directly. - Biking is genuinely viable on the flat Tempe campus...

**Chunk #14 — source: `04_housing_hassayampa.md` (536 chars)**
> # Hassayampa Academic Village (HAV), Tempe Campus ## Who lives here Hassayampa Academic Village houses students from the W. P. Carey School of Business. ... ## Rooms and suites HAV offers double-occupancy accommodations with suite-style bathrooms. Room options include shared rooms with shared baths (3-bed and standard configurations) and private rooms with private baths. Twin XL beds (36x80...

**Chunk #22 — source: `06_sun_devil_fitness.md` (595 chars)**
> # Sun Devil Fitness Complex (SDFC), Tempe Campus The SDFC opened on August 21, 1989... ## Access / membership All fee-paying ASU students are automatically members of the Sun Devil Fitness Complex through their ASU registration fees... ## Weights and cardio - Two weight rooms plus a circuit-training room - Over 100 pieces of cardio equipment...

**Chunk #33 — source: `09_hayden_library.md` (594 chars)**
> ... - **Level One:** the Wurzburger Reading Room and the Luhrs Arizona Reading Room, featured collections... - **Level Two:** book stacks (Sun Devil Reads, Labriola Open Stack...), the Zine Collection... - **Level Three:** the Makerspace, the Map and Geospatial Hub, Naturespace...

Each chunk is a complete, retrievable thought tied to one topic, with its source
filename attached in metadata. No fragments, empty strings, or HTML artifacts
(verified: 0 empty / 0 HTML-leftover chunks across all 40).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers` — runs locally
with no API key or rate limits, 384-dimensional, fast, and strong on short
English passages. Embeddings are L2-normalized and stored in ChromaDB with
cosine distance, so the same vector space is used for documents and queries.

**Why semantic search works here:** queries rarely share exact words with the
source ("how often does the shuttle run" vs. "Shuttles run every 12 to 15
minutes"), but the embedding maps both to nearby vectors by meaning, so the
right chunk is still retrieved.

**Production tradeoff reflection:** If cost weren't a constraint and this served
real students, I'd weigh a larger hosted model (e.g. OpenAI
`text-embedding-3-large` or a Cohere multilingual model). The wins:
**domain-specific accuracy** (ASU jargon like "M&G," "SunCard," "FLASH,"
"Barrett" that MiniLM may treat as low-signal tokens), a **longer context
window** so I could embed bigger chunks without truncation, and **multilingual
support** for ASU's large international population asking in their first
language. The costs: per-query API latency and dollar cost, an external
dependency with rate limits, and sending student queries off-device. For a
small, English, fact-lookup corpus like this, local MiniLM is the right call;
the hosted upgrade pays off mainly at larger scale or with multilingual users.

---

## Retrieval Test Results

Top-k = 4, with a relevance floor: any chunk with cosine distance > 0.75 is
dropped. Distances below are cosine distance (lower = more similar).

**Query 1 — "What is the cheapest student parking permit at Tempe and which lot is it for?"**
| rank | source chunk | distance |
|---|---|---|
| 1 | 02_parking_student_guide | 0.23 |
| 2 | 01_parking_official | 0.31 |
| 3 | 01_parking_official | 0.36 |
| 4 | 02_parking_student_guide | 0.45 |

*Why these are relevant:* the official parking chunk (rank 2–3) contains the
exact price line "Lot 59: $280 ... Lot 59 is the least expensive student
commuter option," which directly answers the question; the student-guide chunks
corroborate that Lot 59 is a cheap commuter option. All four come from the two
parking documents — retrieval routed to the right topic.

**Query 2 — "How do Maroon & Gold (M&G) Dollars work and what's the minimum purchase?"**
| rank | source chunk | distance |
|---|---|---|
| 1 | 03_dining_meal_plans | 0.32 |
| 2 | 03_dining_meal_plans | 0.61 |
| 3 | 03_dining_meal_plans | 0.65 |
| 4 | 03_dining_meal_plans | 0.72 |

*Why these are relevant:* every retrieved chunk is from the dining document, and
the top chunk (dist 0.32) literally defines M&G Dollars as a "dollar-for-dollar,
tax-free declining balance" and states the "$25 minimum" — the precise facts the
query asks for. The clean single-source routing is exactly what we want for a
topic that lives in one document.

**Query 3 — "When does the Safety Escort service run and how do I request one?"**
| rank | source chunk | distance |
|---|---|---|
| 1 | 08_campus_safety | 0.35 |
| 2 | 08_campus_safety | 0.46 |
| 3 | 08_campus_safety | 0.50 |
| 4 | 01_parking_official | 0.69 |

The top three (the safety document) carry the escort hours and request method;
the fourth (parking, dist 0.69) is a weak match that slips in under the 0.75
floor but contributes nothing — the model ignores it.

---

## Grounded Generation

**System prompt grounding instruction (verbatim, from `rag/generate.py`):**
The model is told it answers *only* using the numbered SOURCES in the user
message, with these rules:
> 1. Use only facts stated in the SOURCES. Do not add outside knowledge, even if you think you know the answer.
> 2. After each claim, cite the source(s) it came from using bracketed numbers, e.g. "Shuttles run every 10-15 minutes [2]."
> 3. If the SOURCES do not contain enough information to answer, say exactly: "I don't have enough information in my sources to answer that." Do not guess.
> 4. Keep answers concise and specific. Prefer the wording of the sources over paraphrase when a detail matters (times, prices, names, locations).

**Grounding is enforced two ways:**
1. **Structurally** — the model literally never receives any campus knowledge
   except the numbered retrieved chunks. The prompt is built by
   `_format_context()`, which injects only the retrieved text.
2. **By the prompt rules above**, plus a **retrieval relevance floor** (drop
   distance > 0.75) so that an out-of-corpus query can return zero chunks and
   force an abstention.

**Verification that this actually holds:** I asked three questions the model
unquestionably knows from its training data but that the corpus does *not*
contain — "Who is the president of ASU?", "What year was ASU founded?", "What is
the campus WiFi password?" — and even with 4 chunks retrieved each time, it
refused all three with the exact abstain string. So grounding is enforced at the
prompt level, not merely by the distance filter.

**How source attribution is surfaced:** the LLM cites sources inline with
bracketed numbers ([1], [2], …), and — independently — the interface appends a
**Sources** list built programmatically from each retrieved chunk's metadata
(title + URL). Attribution therefore appears even if the model forgets to cite,
because it is derived from the retrieval result, not left to the LLM.

---

## Example Responses

**Example 1 (with attribution) — "What is the cheapest student parking permit at Tempe and which lot is it for?"**
> The cheapest student parking permit at Tempe is $280 per year, and it is for
> Lot 59 [3]. Lot 59 is also mentioned as one of the go-to commuter areas for
> students because it is one of the cheapest student-accessible options [1].
>
> Sources:
> &nbsp;&nbsp;[1] Surviving ASU Parking — A Student's Practical Guide (Unofficial) https://livesolasu.com/blog/asu-parking-sol/
> &nbsp;&nbsp;[3] ASU Tempe Parking — Permits, Lots, and Prices (Official) https://cfo.asu.edu/pts-parking-tempe

**Example 2 (with attribution) — "When does the Safety Escort service run and how do I request one?"**
> The Safety Escort service runs seven days a week from 7 p.m. to 2 a.m. [1]. To
> request a safety escort, you can open the LiveSafe app [1][2] or call
> 480-965-1515 if the app is unavailable [1]. You will need to share your student
> ID, the number of people, and your location to get a ride [1].
>
> Sources: [1][2] ASU CFO / Student Life — LiveSafe / Safety Escort (Official)

**Example 3 (out-of-scope refusal) — "How much is in-state tuition for engineering?"**
> I don't have enough information in my sources to answer that.

(The corpus does not cover tuition; the system declines rather than guessing.)

---

## Query Interface

Two interfaces share the same end-to-end `answer()` function:

- **CLI** (`python app.py`): interactive REPL; also `python app.py "question"`
  for a single answer, or `python app.py --web` for the web UI.
- **Gradio web UI** (`python app.py --web` → http://localhost:7860): a chat box.

**Input field:** a single free-text question ("Your question").
**Output fields:** the grounded **Answer** (with inline [n] citations) followed
by a **Sources** list (numbered title + URL for each retrieved document).

**Sample interaction transcript:**
```
you > How often does the Tempe FLASH shuttle run and what hours?

The Tempe FLASH shuttle runs every 12 to 15 minutes [1], and it operates
Monday through Friday from 7 a.m. to 10 p.m. [1]. During university holidays
and class breaks, the service is limited to 7 a.m. to 6 p.m. [1].

Sources:
  [1] ASU Public Transit and Shuttles (Official) https://cfo.asu.edu/transit
```

---

## Evaluation Report

| # | Question | Expected answer | System response (summary) | Retrieval quality | Accuracy |
|---|----------|-----------------|---------------------------|-------------------|----------|
| 1 | Cheapest student parking permit + which lot? | $280/year, Lot 59 (cheapest commuter option) | "$280 per year, Lot 59 [3]; also a go-to cheap commuter area [1]" | Relevant (routed to both parking docs) | **Accurate** |
| 2 | How often does FLASH run + hours? | Every 12–15 min, Mon–Fri 7a–10p (7a–6p on breaks) | "Every 12 to 15 minutes [1]; Mon–Fri 7a–10p; 7a–6p on holidays/breaks [1]" | Relevant (top = transit doc) | **Accurate** |
| 3 | How do M&G Dollars work + minimum? | Tax-free dollar-for-dollar balance on the ASU ID; $25 minimum; bonus tiers 5–20% | "Dollar-for-dollar, tax-free balance [1]; $25 minimum [1]; three buckets incl. Bonus M&G [1,3]" | Relevant (all dining doc) | **Accurate** (core facts right; did not surface the exact 5–20% bonus percentages) |
| 4 | Safety Escort hours + how to request? | 7p–2a, 7 days/week; via LiveSafe app or 480-965-1515 | "7 days/week 7p–2a [1]; LiveSafe app [1,2] or 480-965-1515 [1]; share ID/#/location" | Relevant (top 3 = safety doc) | **Accurate** |
| 5 | Who lives in Hassayampa + bed setup? | W. P. Carey students; double-occupancy suite-style; Twin XL 36×80, lofting available | "W. P. Carey students [1]; double-occupancy suite-style; Twin XL 36×80 with lofting [1,2]" | Relevant (all housing doc) | **Accurate** |

**Summary:** 5/5 routed to the correct source document and answered accurately;
the only minor gap is Q3 not surfacing the exact 5–20% bonus-tier percentages
(present in the corpus but in a lower-ranked chunk).

---

## Failure Case Analysis

**Question that failed:** "What is the range of parking permit prices at ASU Tempe?"

**What the system returned:**
> The range of parking permit prices at ASU Tempe is from about $210 to $780 per
> academic year [1][4], with specific prices ranging from $280 for Lot 59 to $950
> for Apache Boulevard, Rural Road, and Tyler Street [2][3].

**Why it's a failure:** the answer **silently merges two conflicting ranges from
two sources of different authority**. "$210 to $780" comes from the *unofficial*
student blog (`02_parking_student_guide`), while the *official* PTS page
(`01_parking_official`) actually lists $280 (Lot 59) up to $950 (Apache/Rural/
Tyler). The response stitches the unofficial figure and the official figures into
one sentence as if they agree, when in fact the blog's range is outdated/wrong
relative to the official page. A student reading this can't tell that "$210" is a
stale rumor and "$280" is the real floor.

**Root cause (tied to a specific pipeline stage):** this is a **retrieval +
generation** failure, not a chunking one. At retrieval, the unofficial blog
chunk ranks **#1** (distance 0.23) purely on embedding similarity — the system
has no notion of source *authority*, so an unofficial source can outrank the
official one. At generation, the model is instructed to use all provided sources
and cite them, but it has **no rule to prefer official sources or to flag
disagreement**, so it dutifully reports both numbers as if complementary. This is
exactly the "stale or conflicting numbers across sources" risk anticipated in
`planning.md`.

**What I would change to fix it:** (1) add a generation rule: *when sources of
different `source_type` give conflicting numbers, prefer `official` and note the
discrepancy*; (2) pass `source_type` into the prompt context (it's already in
metadata) so the model can act on it; (3) optionally re-rank retrieval to break
ties toward official sources. The metadata to do this already exists — only the
prompt and ranking would change.

---

## Spec Reflection

**One way the spec helped:** writing the **Evaluation Plan** (5 specific,
checkable questions) and the **Chunking Strategy** in `planning.md` before coding
gave me concrete acceptance tests. When I built retrieval, I didn't have to guess
whether it "felt right" — I ran the 5 planned questions, saw their top-result
distances, and had an objective signal. Centralizing every tunable (chunk size,
overlap, top-k, distance floor) in `rag/config.py`, as the spec implied, meant
the writeup and the code couldn't drift apart.

**One way the implementation diverged, and why:** the spec originally set chunk
size to **900/150 (27 chunks)**, but the implementation now uses **600/120 (40
chunks)**. I diverged because retrieval testing against the eval questions
revealed that 900-char chunks bundled multiple subtopics, pushing two queries
(FLASH shuttle, M&G Dollars) to a top-result distance of 0.50–0.52 — above the
0.5 "strong match" bar. Testing four chunk sizes showed 600/120 brought every
query's top distance below 0.5 without breaking any answer, so I updated both the
code and the spec's Chunking Strategy to reflect the change and the reason. This
is the spec doing its job: the divergence was driven by evidence, and documented.

---

## AI Usage

> *Note: these describe how I directed an AI coding assistant (Claude) during this
> project. Review and adjust to your own voice before submitting.*

**Instance 1 — chunking implementation, then evidence-driven tuning**
- *What I gave the AI:* my `planning.md` Documents and Chunking Strategy sections
  (file types, the 900/150 spec, "split on natural boundaries") and asked it to
  implement `load_documents()` with front-matter parsing and `chunk_text()`.
- *What it produced:* a boundary-aware chunker that splits on paragraph/sentence
  breaks and only hard-cuts oversized blocks, plus front-matter parsing into
  per-chunk metadata.
- *What I changed/overrode/directed:* after wiring up retrieval, I directed it to
  **test whether the chunk size was right** rather than trust the spec. It
  compared four chunk sizes against my eval questions and showed 900/150 left two
  queries with top distance ≥0.5. I had it adopt **600/120** and update
  `planning.md` with the rationale — overriding my own original spec number based
  on the measured retrieval behavior.

**Instance 2 — grounded generation and adversarial verification**
- *What I gave the AI:* the grounding goal from my spec — answer only from
  retrieved chunks, cite sources by number, abstain when context is insufficient —
  and asked it to write the Groq call and system prompt.
- *What it produced:* the `SYSTEM_PROMPT` with explicit "use only the SOURCES /
  do not add outside knowledge / exact abstain string" rules, and source
  attribution appended programmatically from metadata.
- *What I changed/overrode/directed:* I wasn't satisfied that the out-of-vocab
  abstention proved grounding, so I directed it to **stress-test with questions
  the model knows from training but the corpus lacks** (ASU's president, founding
  year, WiFi password). All three were correctly refused, confirming the prompt —
  not just the distance filter — enforces grounding.

---

## Running it

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env          # then add your GROQ_API_KEY
python build_index.py          # ingest -> chunk -> embed -> store (local, no key)
python app.py                  # interactive CLI   (or: --web for the Gradio UI)
```
