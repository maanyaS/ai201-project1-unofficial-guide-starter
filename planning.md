# Project 1 Planning: The Unofficial Guide

> Write this document before you write any pipeline code.
> Your spec and architecture diagram are what you'll use to direct AI tools (Claude, Copilot, etc.) to generate your implementation — the more specific they are, the more useful the generated code will be.
> Update the Retrieval Approach and Chunking Strategy sections if you change your approach during implementation.
> Update this file before starting any stretch features.

---

## Domain

<!-- What domain did you choose? Why is this knowledge valuable and hard to find through official channels? -->
My system covers reviews and information regarding Computer Science professors at Rutgers University New Brunswick. My source will be able to answer questions regarding whether a professor is good at teaching and guarantees student success and vice versa. This knowledge is valuable, since there is no official Rutgers website that provides information regarding professors and their corresponding students' success.

---

## Documents

<!-- List your specific sources: URLs, subreddit names, forum threads, or file descriptions.
     Aim for at least 10 sources that together cover different subtopics or perspectives within your domain. -->
https://www.ratemyprofessors.com/professor/2875899 — Apoorva Goel
https://www.ratemyprofessors.com/professor/3066620 — Tina Burns
https://www.ratemyprofessors.com/professor/720556 — Abeer Elahraf
https://www.ratemyprofessors.com/professor/2297066 — Wesley Cowan
https://www.ratemyprofessors.com/professor/2336289 — David Menendez
https://www.ratemyprofessors.com/professor/2414859 — Ananda Gunawardena
https://www.ratemyprofessors.com/professor/52112 — Mario Szegedy
https://www.ratemyprofessors.com/professor/381323 — Rajiv Gandhi
https://www.ratemyprofessors.com/professor/409364 — Casimir Kulikowski
https://www.ratemyprofessors.com/professor/2925139 — John Blackmore


| # | Source | Description | URL or location |
|---|--------|-------------|-----------------|
| 1 | Rate my Professor | Provides ratings for Professor Apoorva Goel | https://www.ratemyprofessors.com/professor/2875899 |
| 2 | Rate my Professor | Provides ratings for Professor Tina Burns | https://www.ratemyprofessors.com/professor/3066620 |
| 3 | Rate my Professor | Provides ratings for Professor Abeer Elahraf | https://www.ratemyprofessors.com/professor/720556 |
| 4 | Rate my Professor | Provides ratings for Professor Wesley Cowan | https://www.ratemyprofessors.com/professor/2297066 |
| 5 | Rate my Professor | Provides ratings for Professor David Menendez | https://www.ratemyprofessors.com/professor/2336289 |
| 6 | Rate my Professor | Provides ratings for Professor Ananda Gunawardena | https://www.ratemyprofessors.com/professor/2414859 |
| 7 | Rate my Professor | Provides ratings for Professor Mario Szegedy | https://www.ratemyprofessors.com/professor/52112 |
| 8 | Rate my Professor | Provides ratings for Professor Rajiv Gandhi | https://www.ratemyprofessors.com/professor/381323 |
| 9 | Rate my Professor | Provides ratings for Professor Casimir Kulikowski | https://www.ratemyprofessors.com/professor/409364 |
| 10 | Rate my Professor | Provides ratings for Professor John Blackmore | https://www.ratemyprofessors.com/professor/2925139 |

---

## Chunking Strategy

<!-- How will you split documents into chunks?
     State your chunk size (in tokens or characters), overlap size, and explain why those
     numbers fit the structure of your documents.
     A review-heavy corpus warrants different chunking than a long FAQ. -->

**Chunk size:300-500 characters**

**Overlap: 50-75 characters**
 
**Reasoning: Each review is only one-four sentences long. In a chunk size of 300-500 characters, one or two reviews will be fit in. If a review got separated into 2 chunks, an overlap of 50-75 characters allows for context from the first chunk of the review to be accounted for.**

---

## Retrieval Approach

<!-- Which embedding model are you using (e.g., all-MiniLM-L6-v2 via sentence-transformers)?
     How many chunks will you retrieve per query (top-k)?
     If you were deploying this for real users and cost wasn't a constraint, what tradeoffs
     would you weigh in choosing a different embedding model — context length, multilingual
     support, accuracy on domain-specific text, latency? -->

**Embedding model: all-MiniLM-L6-v2 via sentence-transformers**

**Top-k: 5**

**Production tradeoff reflection:**
If cost wasn't a constraint, I'd weigh accuracy on short informal text as RMP reviews are casual and full of slang. A model fine-tuned on social/forum text (like Reddit-trained variants) would outperform a general-purpose model here

---

## Evaluation Plan

<!-- List your 5 test questions with their expected correct answers.
     Questions should be specific enough that you can judge whether the system's response
     is right or wrong. "What are good dining halls?" is too vague.
     "What do students say about wait times at [dining hall name] during lunch?" is testable. -->

| # | Question | Expected answer |
|---|----------|-----------------|
| 1 | What do students say about Menendez's exams in CS214?| Exams are conceptual and trivia-based with little coding, and that homeworks are very difficult and heavily weighted|
| 2 | Which CS professor is most often described as giving good feedback| Abeer Elahraf, who is explicitly tagged "gives good feedback" and praised for being helpful and clear|
| 3 | Is Tina Burns recommended for CS211?| Yes, students consistently say she's kind, gives lots of extra credit, and makes the course low-stress|
| 4 | Which CS professor has the lowest "would take again" percentage among the 10 sources?| Casimir Kulikowski at 6% would take again|
| 5 | What do students say about Ananda Gunawardena's organization?| Reviews note he is disorganized and uncoordinated but enthusiastic, patient with questions, and good at explaining concepts|

---

## Anticipated Challenges

<!-- What could go wrong? Name at least two specific risks with reasoning.
     Consider: noisy or inconsistent documents, missing source attribution, off-topic
     retrieval, chunks that split key information across boundaries. -->

1. Inconsistent formatting across manually copied text is a risk.
When I copy-paste from RMP, different reviews may come out with inconsistent spacing, line breaks, or stray characters depending on how you copy them. This means my chunking function can't assume clean, uniform input. Mitigation: before building the pipeline, open each .txt file and do a quick visual scan to make sure reviews are clearly separated — add a blank line between each review if they aren't, so my chunker has a reliable delimiter to split on.



2. Retrieved chunks may mention the wrong professor.
If a review says "unlike Professor X, Menendez does..." and gets retrieved for a query about Professor X, my system will surface misleading information. Mitigation: attach professor name as metadata to every chunk and filter retrieval by professor when the query names one specifically.


---

## Architecture

<!-- Draw a diagram of your pipeline showing the five stages:
     Document Ingestion → Chunking → Embedding + Vector Store → Retrieval → Generation
     Label each stage with the tool or library you're using.
     You can use ASCII art, a Mermaid diagram, or embed a sketch as an image.
     You'll use this diagram as context when prompting AI tools to implement each stage. -->
┌─────────────────────┐
│  Document Ingestion │  ← manually copy-pasted RMP reviews
│  10 local .txt files│    loaded with Python open() / os.listdir()
└────────┬────────────┘
         │  raw review text + metadata (prof name, course, rating)
         ▼
┌─────────────────────┐
│     Chunking        │  ← custom Python function chunk_text()
│  1 review = 1 chunk │    fallback: 500 char / 75 char overlap
│  + metadata tagged  │
└────────┬────────────┘
         │  list of chunk dicts
         ▼
┌──────────────────────────┐
│  Embedding + Vector Store│  ← sentence-transformers all-MiniLM-L6-v2
│                          │    + ChromaDB (local, no setup overhead)
└────────┬─────────────────┘
         │  vector index
         ▼
┌─────────────────────┐
│     Retrieval       │  ← ChromaDB similarity search, top-k = 5
│                     │    optional metadata filter by professor name
└────────┬────────────┘
         │  5 most relevant review chunks
         ▼
┌─────────────────────┐
│     Generation      │  ← Claude API (claude-haiku for speed/cost)
│                     │    prompt = retrieved chunks + user question
└─────────────────────┘
         │
         ▼
    answer with citations
---

## AI Tool Plan

<!-- For each part of the pipeline below, describe:
     - Which AI tool you plan to use (Claude, Copilot, ChatGPT, etc.)
     - What you'll give it as input (which sections of this planning.md, which requirements)
     - What you expect it to produce
     - How you'll verify the output matches your spec

     "I'll use AI to help me code" is not a plan.
     "I'll give Claude my Chunking Strategy section and ask it to implement chunk_text()
     with my specified chunk size and overlap" is a plan. -->

Stage 1 — Document Ingestion

Tool: Claude
Input: tell Claude I have 10 .txt files named by professor (e.g. goel_apoorva.txt), each containing copy-pasted RMP reviews separated by blank lines
Ask it to: write load_documents.py that reads each file, splits on blank lines into individual reviews, and attaches the professor name (derived from the filename) as metadata
Verify: print the first 3 chunks from one file and confirm the professor name metadata is correct and the text looks clean

Stage 2 — Chunking

Tool: Claude
Input: give Claude the Chunking Strategy section (one review = one chunk, 500 char fallback, 75 overlap)
Ask it to: implement chunk_text(reviews: list[dict]) -> list[dict] that returns chunks with metadata preserved
Verify: print chunk lengths and confirm none exceed 500 characters and that professor name is present on every chunk

Stage 3 — Embedding + Vector Store

Tool: Claude
Input: give Claude the Architecture diagram and embedding model choice
Ask it to: write embed_and_store.py using sentence-transformers and ChromaDB that ingests the chunk list and builds a local vector store
Verify: confirm ChromaDB collection has the same number of entries as my total chunk count

Stage 4 — Retrieval + Generation

Tool: Claude
Input: give Claude the full Architecture section, the top-k value, and the generation model choice
Ask it to: write query.py that takes a plain-language question, retrieves top-5 chunks from ChromaDB, formats them into a prompt, and calls the Claude API to generate a cited answer
Verify: run my 5 evaluation questions and check responses against my expected answers table

**Milestone 3 — Ingestion and chunking:**

**Milestone 4 — Embedding and retrieval:**

**Milestone 5 — Generation and interface:**
