"""
embed_and_retrieve.py

Milestone 4: Embed chunks and load into ChromaDB, then test retrieval.

Pipeline stage:
  chunks.json (from ingest_and_chunk.py)
      → sentence-transformers all-MiniLM-L6-v2 (embed)
      → ChromaDB local vector store (store)
      → retrieval function (query)

Run this file directly to:
  1. Load chunks from chunks.json
  2. Embed and store in ChromaDB
  3. Test retrieval with 3 evaluation queries
"""

import json
import os
import chromadb
from sentence_transformers import SentenceTransformer

# ── Configuration (matches planning.md) ──────────────────────────────────────
CHUNKS_FILE = "chunks.json"           # output from ingest_and_chunk.py
CHROMA_DIR = "chroma_store"           # local folder ChromaDB persists to
COLLECTION_NAME = "rutgers_cs_profs"
EMBEDDING_MODEL = "all-MiniLM-L6-v2"
TOP_K = 5


# ── Step 1: Load chunks from JSON ─────────────────────────────────────────────
def load_chunks(chunks_file: str) -> list[dict]:
    if not os.path.exists(chunks_file):
        raise FileNotFoundError(
            f"'{chunks_file}' not found. Run ingest_and_chunk.py first."
        )
    with open(chunks_file, "r", encoding="utf-8") as f:
        chunks = json.load(f)
    print(f"✓ Loaded {len(chunks)} chunks from '{chunks_file}'")
    return chunks


# ── Step 2: Set up embedding model ───────────────────────────────────────────
def load_embedding_model(model_name: str = EMBEDDING_MODEL) -> SentenceTransformer:
    print(f"\nLoading embedding model '{model_name}'...")
    print("  (First run will download ~90MB — subsequent runs are instant)")
    model = SentenceTransformer(model_name)
    print(f"✓ Model loaded")
    return model


# ── Step 3: Set up ChromaDB ───────────────────────────────────────────────────
def setup_chroma(persist_dir: str = CHROMA_DIR) -> chromadb.Collection:
    """
    Creates (or loads) a local ChromaDB collection.
    ChromaDB stores your vectors on disk in chroma_store/ so they
    persist between runs — you only embed once.
    """
    client = chromadb.PersistentClient(path=persist_dir)

    # Delete existing collection if it exists, so re-runs start fresh
    existing = [c.name for c in client.list_collections()]
    if COLLECTION_NAME in existing:
        client.delete_collection(COLLECTION_NAME)
        print(f"  Cleared existing collection '{COLLECTION_NAME}'")

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"}  # cosine similarity (lower = more similar)
    )
    print(f"✓ ChromaDB collection '{COLLECTION_NAME}' ready at '{persist_dir}/'")
    return collection


# ── Step 4: Embed and store all chunks ───────────────────────────────────────
def embed_and_store(
    chunks: list[dict],
    model: SentenceTransformer,
    collection: chromadb.Collection,
) -> None:
    """
    Embeds each chunk's text and stores it in ChromaDB with metadata.
    Metadata stored per chunk: professor name, source filename, chunk_index.
    """
    print(f"\nEmbedding {len(chunks)} chunks...")

    texts = [chunk["text"] for chunk in chunks]
    embeddings = model.encode(texts, show_progress_bar=True)

    # ChromaDB requires string IDs
    ids = [f"chunk_{i}" for i in range(len(chunks))]

    metadatas = [
        {
            "professor": chunk["professor"],
            "source": chunk["source"],
            "chunk_index": chunk["chunk_index"],
        }
        for chunk in chunks
    ]

    # Add in batches of 100 to avoid memory issues with large corpora
    batch_size = 100
    for i in range(0, len(chunks), batch_size):
        batch_end = min(i + batch_size, len(chunks))
        collection.add(
            ids=ids[i:batch_end],
            embeddings=embeddings[i:batch_end].tolist(),
            documents=texts[i:batch_end],
            metadatas=metadatas[i:batch_end],
        )

    # Verify count matches
    stored_count = collection.count()
    print(f"✓ Stored {stored_count} chunks in ChromaDB")

    if stored_count != len(chunks):
        print(f"⚠  WARNING: Expected {len(chunks)} but stored {stored_count} — check for duplicates")


# ── Step 5: Retrieval function ────────────────────────────────────────────────
def retrieve(
    query: str,
    model: SentenceTransformer,
    collection: chromadb.Collection,
    top_k: int = TOP_K,
    professor_filter: str = None,
) -> list[dict]:
    """
    Embeds the query and returns the top_k most similar chunks.

    Args:
        query:            Plain-language question from the user
        model:            The same embedding model used at index time
        collection:       ChromaDB collection to search
        top_k:            Number of results to return (default 5)
        professor_filter: Optional — restrict results to one professor by name
                          e.g. professor_filter="David Menendez"

    Returns:
        List of dicts with keys: text, professor, source, chunk_index, distance
    """
    query_embedding = model.encode([query])[0].tolist()

    # Optional metadata filter (mitigates cross-professor contamination risk
    # identified in planning.md Anticipated Challenges)
    where_filter = None
    if professor_filter:
        where_filter = {"professor": {"$eq": professor_filter}}

    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter,
        include=["documents", "metadatas", "distances"],
    )

    # Flatten ChromaDB's nested result format into a clean list
    retrieved = []
    for text, metadata, distance in zip(
        results["documents"][0],
        results["metadatas"][0],
        results["distances"][0],
    ):
        retrieved.append({
            "text": text,
            "professor": metadata["professor"],
            "source": metadata["source"],
            "chunk_index": metadata["chunk_index"],
            "distance": round(distance, 4),
        })

    return retrieved


# ── Step 6: Print retrieval results for inspection ───────────────────────────
def print_retrieval_results(query: str, results: list[dict]) -> None:
    print(f"\n{'='*55}")
    print(f"QUERY: {query}")
    print(f"{'='*55}")

    for i, result in enumerate(results, 1):
        distance = result["distance"]

        # Flag weak matches per milestone guidance (>0.5 = concern, >0.6 = bad)
        if distance > 0.6:
            quality = "❌ WEAK MATCH"
        elif distance > 0.5:
            quality = "⚠  BORDERLINE"
        else:
            quality = "✓  GOOD MATCH"

        print(f"\n  Result {i} — {quality} (distance: {distance})")
        print(f"  Professor : {result['professor']}")
        print(f"  Source    : {result['source']}")
        print(f"  Text      : {result['text']}")


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":

    # --- Load and embed ---
    chunks = load_chunks(CHUNKS_FILE)
    model = load_embedding_model()
    collection = setup_chroma()
    embed_and_store(chunks, model, collection)

    # --- Test retrieval with all 5 evaluation plan queries ---
    # These come directly from planning.md Evaluation Plan.
    #
    # Queries that name a specific professor use professor_filter to restrict
    # retrieval to that professor's chunks only. This fixes cross-professor
    # contamination (Anticipated Challenge #2 in planning.md) where semantically
    # similar intro-CS reviews from the wrong professor rank highly.
    #
    # Queries that ask across all professors (e.g. "which professor gives the
    # best feedback") do NOT use a filter — we want results from any professor.
    test_queries = [
        {
            "query": "What do students say about Menendez's exams in CS214?",
            "professor_filter": "David Menendez",  # named professor → filter
        },
        {
            "query": "Which CS professor is most often described as giving good feedback?",
            "professor_filter": None,               # cross-professor → no filter
        },
        {
            "query": "Is Tina Burns recommended for CS211?",
            "professor_filter": "Tina Burns",       # named professor → filter
        },
        {
            "query": "What do students say about Rajiv Gandhi's teaching pace?",
            "professor_filter": "Rajiv Gandhi",     # named professor → filter
        },
        {
            "query": "What do students say about Ananda Gunawardena's organization?",
            "professor_filter": "Ananda Gunawardena",  # named professor → filter
        },
    ]

    print("\n" + "="*55)
    print("RETRIEVAL TEST — all 5 evaluation plan queries")
    print("="*55)
    print("Inspect each result: is it relevant? Is the distance below 0.5?")

    for item in test_queries:
        results = retrieve(
            query=item["query"],
            model=model,
            collection=collection,
            professor_filter=item["professor_filter"],
        )
        print_retrieval_results(item["query"], results)

        # Extra cross-check: warn if any result is from the wrong professor
        if item["professor_filter"]:
            wrong = [r for r in results if r["professor"] != item["professor_filter"]]
            if wrong:
                print(f"\n  ⚠  CONTAMINATION: {len(wrong)} result(s) from wrong professor:")
                for r in wrong:
                    print(f"     → {r['professor']} (distance: {r['distance']})")
            else:
                print(f"\n  ✓ All results are from {item['professor_filter']}")

    print("\n" + "="*55)
    print("CHECKPOINT")
    print("="*55)
    print("✓ Good: top results are on-topic, distance < 0.5, correct professor")
    print("⚠  Bad: off-topic results, or distance > 0.6 on top result")
    print("   → If retrieval looks wrong, check chunks.json for bad chunks")
    print("   → before moving to Milestone 5 (generation)")