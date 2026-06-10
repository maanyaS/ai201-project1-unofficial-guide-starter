# The Unofficial Guide — Project 1

> **How to use this template:**
> Complete each section *after* you've built and tested the corresponding part of your system.
> Do not write placeholder text — if a section isn't done yet, leave it blank and come back.
> Every section below is required for submission. One-liners will not receive full credit.

---

## Domain

My system covers reviews and information regarding Computer Science professors at Rutgers University New Brunswick. My source will be able to answer questions regarding whether a professor is good at teaching and guarantees student success and vice versa. This knowledge is valuable, since there is no official Rutgers website that provides information regarding professors and their corresponding students' success.

---
<div>
    <a href="https://www.loom.com/share/6caba1124b9c4d21933902c10e2f81d5">
      <p>Videos | Library | Loom - 10 June 2026 - Watch Video</p>
    </a>
    <a href="https://www.loom.com/share/6caba1124b9c4d21933902c10e2f81d5">
      <img style="max-width:300px;" src="https://cdn.loom.com/sessions/thumbnails/6caba1124b9c4d21933902c10e2f81d5-f46aeaea8f310d39-full-play.gif#t=0.1">
    </a>
  </div>
  
## Document Sources

| # | Source | Type | URL or file path |
|---|--------|------|-----------------|
| 1 | Rate My Professors — Apoorva Goel | Student reviews | https://www.ratemyprofessors.com/professor/2875899 |
| 2 | Rate My Professors — Tina Burns | Student reviews | https://www.ratemyprofessors.com/professor/3066620 |
| 3 | Rate My Professors — Abeer Elahraf | Student reviews | https://www.ratemyprofessors.com/professor/720556 |
| 4 | Rate My Professors — Wesley Cowan | Student reviews | https://www.ratemyprofessors.com/professor/2297066 |
| 5 | Rate My Professors — David Menendez | Student reviews | https://www.ratemyprofessors.com/professor/2336289 |
| 6 | Rate My Professors — Ananda Gunawardena | Student reviews | https://www.ratemyprofessors.com/professor/2414859 |
| 7 | Rate My Professors — Mario Szegedy | Student reviews | https://www.ratemyprofessors.com/professor/52112 |
| 8 | Rate My Professors — Rajiv Gandhi | Student reviews | https://www.ratemyprofessors.com/professor/381323 |
| 9 | Rate My Professors — Casimir Kulikowski | Student reviews | https://www.ratemyprofessors.com/professor/409364 |
| 10 | Rate My Professors — John Blackmore | Student reviews | https://www.ratemyprofessors.com/professor/2925139 |

---

## Chunking Strategy

**Chunk size:** 500 characters

**Overlap:** 75 characters

**Why these choices fit your documents:** Each RMP review is naturally short — typically one to four sentences. The primary chunking strategy treats one review as one chunk, since each review is a self-contained unit of student opinion. The 500-character limit serves as a fallback for unusually long reviews, with 75 characters of overlap to preserve context if a review is split at a boundary. This approach keeps each chunk semantically coherent and avoids merging unrelated opinions from different students into a single chunk. Before chunking, documents were cleaned to remove RMP boilerplate such as star rating UI labels, navigation text, and HTML entities, so only the actual student-written review text was retained.

**Final chunk count:** 127 chunks across all 10 documents (varies based on how many reviews were copy-pasted per professor).

---

## Embedding Model

**Model used:** `all-MiniLM-L6-v2` via `sentence-transformers`, run locally with no API key.

**Production tradeoff reflection:** For a beginner project with short, informal review text, `all-MiniLM-L6-v2` is sufficient — it is fast, free, and runs entirely locally. However, if deploying for real users, several tradeoffs would need to be weighed. First, accuracy on informal text: RMP reviews are casual and full of slang, so a model fine-tuned on social or forum text would likely outperform a general-purpose model. Second, context length: `all-MiniLM-L6-v2` caps at 256 tokens, which is fine for individual reviews but would fail if longer documents were added later. A model like OpenAI's `text-embedding-3-small` handles up to 8,191 tokens. Third, latency: larger models such as `instructor-xl` are more accurate but noticeably slower at query time, which matters in a user-facing product. For this project, the local, no-cost model was the right fit given the time constraint and document size.

---

## Grounded Generation

**System prompt grounding instruction:** The system prompt explicitly instructs the model to answer using only the information provided in the retrieved sources and to decline if the sources are insufficient: *"Answer the question using ONLY the information provided in the sources below. Do not use any outside knowledge or make assumptions beyond what is written. If the sources do not contain enough information to answer the question, respond with: 'I don't have enough information in my documents to answer that.'"* The model is also instructed to cite every claim using the format `(Source: filename)`. The Groq LLaMA model is called at a temperature of 0.2 to reduce hallucination and keep responses faithful to the retrieved text.

**How source attribution is surfaced in the response:** Source attribution is handled in two ways. First, the model is prompted to inline-cite every claim with the source filename. Second, source filenames are collected programmatically from the retrieved chunk metadata after generation — not left to the LLM to add on its own — and displayed separately in the "Retrieved from" box in the Gradio UI. This ensures attribution appears even if the model fails to cite inline.

---

## Evaluation Report

| # | Question | Expected answer | System response (summarized) | Retrieval quality | Response accuracy |
|---|----------|-----------------|------------------------------|-------------------|-------------------|
| 1 | What do students say about Menendez's exams in CS214? | Exams are conceptual and trivia-based with little coding, and homeworks are very difficult and heavily weighted | Students say tests resemble trivia exams with random questions and little coding, though one review mentions code-on-paper for midterm and final. The final was noted as fair by one student. The system also flagged that CS214 is not explicitly mentioned in the source text. | Relevant — all chunks from menendez_david.txt | Partially accurate — correctly captured the trivia/low-coding nature of exams but did not mention that homeworks are heavily weighted, which was part of the expected answer |
| 2 | Which CS professor is most often described as giving good feedback? | Abeer Elahraf, who is explicitly tagged "gives good feedback" and praised for being helpful and clear | I don't have enough information in my documents to answer that. | Irrelevant — retrieved chunks from Menendez, Szegedy, Gunawardena, Blackmore, Gandhi Elahraf, Goel, Blackmore, and Gunawardena | Inaccurate — Elahraf is the correct answer based on her explicit "gives good feedback" RMP tag, but the system may have gotten confused since a lot of the other professors also received positive reviews regarding giving students good feedback. |
| 3 | Is Tina Burns recommended for CS211? | Yes — students consistently say she's kind, gives lots of extra credit, and makes the course low-stress | Yes, the system confirmed Burns is recommended, citing extra credit opportunities, straightforward exams, and her understanding demeanor. All retrieved chunks were from burns_tina.txt. | Relevant — all chunks correctly from burns_tina.txt | Accurate |
| 4 | What do students say about Rajiv Gandhi's teaching pace? | Students say he moves very quickly regardless of whether anyone understands, and his accent makes it harder to follow | Students say Gandhi's pace is quick, with multiple reviewers noting he moves fast regardless of comprehension. The accent point was not mentioned in the summarized response. | Relevant — all chunks from gandhi_rajiv.txt | Partially accurate — correctly captured the fast pace but missed the accent detail from the expected answer |
| 5 | What do students say about Ananda Gunawardena's organization? | Reviews note he is disorganized and uncoordinated but enthusiastic, patient with questions, and good at explaining concepts | The system reported mixed opinions — some students called him disorganized and noted conflicting information from him and his TAs, while others did not mention organizational issues. Enthusiasm and patience were not surfaced. | Relevant — all chunks from gunawardena_ananda.txt | Partially accurate — disorganization was correctly captured but the positive traits from the expected answer (enthusiasm, patience, strong concept explanation) were not included |

**Retrieval quality:** Relevant / Partially relevant / Off-target  
**Response accuracy:** Accurate / Partially accurate / Inaccurate

---

## Failure Case Analysis

**Question that failed:** "Which CS professor is most often described as giving good feedback?"

**What the system returned:** I don't have enough information in my documents to answer that.

**Root cause (tied to a specific pipeline stage):** The query has no professor filter, so ChromaDB retrieves chunks from across all 10 professors. The phrase "giving good feedback" doesn't appear verbatim in most review text — students write things like "explains clearly," "helpful," "answers questions well" rather than the exact words "good feedback." The embedding model couldn't find chunks semantically close enough to the query to confidently match, so the retrieved chunks had high distance scores. When the LLM received those weakly-matched chunks and saw nothing that directly addressed "giving good feedback," it followed the grounding instruction and declined to answer rather than guessing.

**What you would change to fix it:** Storing structured RMP tags (like "gives good feedback") as separate, explicitly labeled metadata fields — rather than embedding them as plain text mixed in with review prose — would allow the retriever to surface them more reliably. Alternatively, increasing top-k for cross-professor queries would bring in more Elahraf chunks and give the LLM a better signal.

---

## Spec Reflection

**One way the spec helped you during implementation:** Deciding on a chunk-by-review strategy in planning.md before writing any code was valuable because it clarified that the chunking logic needed to split on blank lines between reviews rather than on fixed character boundaries. Without that decision made in advance, the default approach would have been a mechanical character-count split, which would have cut individual reviews in half and produced fragments with no standalone meaning. Having the spec written first meant the implementation had a clear target to match rather than being designed on the fly.

**One way your implementation diverged from the spec, and why:** The planning.md spec stated a chunk size of 300–500 characters. During implementation, this was narrowed to a fixed 500-character limit, because code requires a single numeric cutoff rather than a range. The 500-character value was chosen as the upper bound of the range to avoid splitting short reviews unnecessarily. The planning.md was updated after implementation to reflect this change and document the reason.

---

## AI Usage

**Instance 1**

- *What I gave the AI:* The Chunking Strategy section and Architecture diagram from planning.md, along with the file naming convention for the 10 .txt files.
- *What it produced:* A complete `ingest_and_chunk.py` script with functions for loading documents, cleaning RMP boilerplate, splitting on blank lines, applying the 500-character fallback with 75-character overlap, and saving output to `chunks.json`. It also included a chunk count validation check and a 5-chunk random inspection printout.
- *What I changed or overrode:* The script used `DOCS_DIR = "docs"` but my project folder was named `documents`. I updated the config variable to match my actual directory name.

**Instance 2**

- *What I gave the AI:* The output of running embed_and_retrieve.py, which showed that the query "Is Tina Burns recommended for CS211?" was returning chunks from goel_apoorva.txt instead of burns_tina.txt.
- *What it produced:* A diagnosis of the cross-professor contamination problem and a fix: the test query block was updated to pass `professor_filter="Tina Burns"` to the retrieve() function for any query that names a specific professor. It also added a contamination warning that prints if any returned chunk is from the wrong professor.
- *What I changed or overrode:* The fix was applied as suggested. I also extended the same professor-filter logic to the other named-professor queries in the test block (Menendez, Gandhi, Gunawardena) since the same contamination risk applied to all of them.
