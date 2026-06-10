"""
query.py

Milestone 5: Wire up generation.

Takes a plain-language question, retrieves the top-k most relevant chunks
from ChromaDB, and passes them to Groq's LLaMA model with a grounding
prompt that forces answers to come only from the retrieved documents.

Usage:
    from query import ask
    result = ask("Is Tina Burns recommended for CS211?")
    print(result["answer"])
    print(result["sources"])

Or run directly:
    python query.py
"""

import os
from dotenv import load_dotenv
from groq import Groq
import chromadb
from sentence_transformers import SentenceTransformer

load_dotenv()

# ── Configuration ─────────────────────────────────────────────────────────────
CHROMA_DIR = "chroma_store"
COLLECTION_NAME = "rutgers_cs_profs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5
GROQ_MODEL = "llama-3.3-70b-versatile"

# ── Load shared resources once at module level ────────────────────────────────
# These are loaded once when query.py is imported, not on every call.
print("Loading embedding model...")
_embedding_model = SentenceTransformer(EMBEDDING_MODEL)

print("Connecting to ChromaDB...")
_chroma_client = chromadb.PersistentClient(path=CHROMA_DIR)
_collection = _chroma_client.get_collection(COLLECTION_NAME)

print("Connecting to Groq...")
_groq_client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

print("✓ Ready\n")


# ── Retrieval ─────────────────────────────────────────────────────────────────
def retrieve_chunks(query: str, professor_filter: str = None) -> list[dict]:
    """
    Embeds the query and retrieves top-k chunks from ChromaDB.
    If a professor name is detected in the query, filters to that professor only.
    """
    query_embedding = _embedding_model.encode([query])[0].tolist()

    where_filter = None
    if professor_filter:
        where_filter = {"professor": {"$eq": professor_filter}}

    results = _collection.query(
        query_embeddings=[query_embedding],
        n_results=TOP_K,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    chunks = []
    for text, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        chunks.append({
            "text": text,
            "professor": metadata["professor"],
            "source": metadata["source"],
            "distance": round(distance, 4),
        })

    return chunks


def detect_professor_filter(query: str) -> str | None:
    """
    Checks if the query names one of the 10 professors.
    If so, returns their full name for use as a metadata filter.
    This prevents cross-professor contamination (planning.md Challenge #2).
    """
    known_professors = [
        "Apoorva Goel",
        "Tina Burns",
        "Abeer Elahraf",
        "Wesley Cowan",
        "David Menendez",
        "Ananda Gunawardena",
        "Mario Szegedy",
        "Rajiv Gandhi",
        "Casimir Kulikowski",
        "John Blackmore",
    ]
    query_lower = query.lower()
    for prof in known_professors:
        # Check last name or full name
        last_name = prof.split()[-1].lower()
        if last_name in query_lower or prof.lower() in query_lower:
            return prof
    return None


# ── Prompt builder ────────────────────────────────────────────────────────────
def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    Builds the context block passed to the LLM.
    Each chunk is labeled with its source file so the model can cite it.
    """
    context_blocks = []
    for i, chunk in enumerate(chunks, 1):
        context_blocks.append(
            f"[Source {i}: {chunk['source']} — {chunk['professor']}]\n{chunk['text']}"
        )
    context = "\n\n".join(context_blocks)

    return f"""You are an assistant that helps Rutgers students learn about CS professors based on student reviews.

Answer the question using ONLY the information provided in the sources below.
Do not use any outside knowledge or make assumptions beyond what is written.
If the sources do not contain enough information to answer the question, respond with:
"I don't have enough information in my documents to answer that."

For every claim you make, cite the source it came from using the format (Source: filename).

---
{context}
---

Question: {query}

Answer:"""


# ── Generation ────────────────────────────────────────────────────────────────
def generate_answer(prompt: str) -> str:
    """Calls Groq LLaMA with the grounded prompt."""
    response = _groq_client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,   # low temperature = more faithful to retrieved text
        max_tokens=512,
    )
    return response.choices[0].message.content.strip()


# ── Main ask() function ───────────────────────────────────────────────────────
def ask(question: str) -> dict:
    """
    End-to-end RAG function. Called by app.py.

    Returns:
        {
            "answer":  str,         grounded LLM response with inline citations
            "sources": list[str],   deduplicated list of source filenames
            "chunks":  list[dict],  raw retrieved chunks (for debugging)
        }
    """
    # 1. Detect if query names a specific professor → apply filter
    professor_filter = detect_professor_filter(question)

    # 2. Retrieve relevant chunks
    chunks = retrieve_chunks(question, professor_filter=professor_filter)

    # 3. Build grounded prompt
    prompt = build_prompt(question, chunks)

    # 4. Generate answer
    answer = generate_answer(prompt)

    # 5. Collect sources — deduplicated, programmatically guaranteed
    #    (not left to the LLM to add on its own)
    sources = list(dict.fromkeys(chunk["source"] for chunk in chunks))

    return {
        "answer": answer,
        "sources": sources,
        "chunks": chunks,   # included for debugging, not shown in UI
    }


# ── CLI test ──────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    # Test all 5 evaluation plan queries from planning.md
    test_queries = [
        "What do students say about Menendez's exams in CS214?",
        "Which CS professor is most often described as giving good feedback?",
        "Is Tina Burns recommended for CS211?",
        "What do students say about Rajiv Gandhi's teaching pace?",
        "What do students say about Ananda Gunawardena's organization?",
    ]

    # Grounding failure test — ask something not in the documents
    out_of_scope = "What is the best dining hall near the CS building?"

    all_queries = test_queries + [out_of_scope]

    for question in all_queries:
        print(f"\n{'='*60}")
        print(f"Q: {question}")
        print(f"{'='*60}")
        result = ask(question)
        print(f"\nANSWER:\n{result['answer']}")
        print(f"\nSOURCES: {', '.join(result['sources'])}")