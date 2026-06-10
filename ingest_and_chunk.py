"""
ingest_and_chunk.py

Loads 10 local .txt files of copy-pasted RMP reviews, cleans them,
and splits them into chunks per the planning.md spec:
  - 1 review = 1 chunk (primary strategy)
  - 500 character fallback with 75 character overlap for long reviews
  - Professor name attached as metadata, derived from filename

Expected file naming convention: firstname_lastname.txt
  e.g. goel_apoorva.txt, burns_tina.txt

Each .txt file should have reviews separated by blank lines.
"""

import os
import re

# ── Configuration (matches planning.md) ──────────────────────────────────────
DOCS_DIR = "documents"          # folder containing your 10 .txt files
MAX_CHUNK_CHARS = 500      # fallback max chunk size
OVERLAP_CHARS = 75         # overlap for fallback splitting


# ── Step 1: Load raw text from all .txt files ─────────────────────────────────
def load_documents(docs_dir: str) -> list[dict]:
    """
    Reads every .txt file in docs_dir.
    Returns a list of dicts: {professor, raw_text}
    Professor name is derived from filename (e.g. goel_apoorva -> Apoorva Goel)
    """
    documents = []

    if not os.path.exists(docs_dir):
        raise FileNotFoundError(
            f"Directory '{docs_dir}' not found. "
            "Create it and place your 10 .txt files inside."
        )

    txt_files = [f for f in os.listdir(docs_dir) if f.endswith(".txt")]

    if not txt_files:
        raise ValueError(f"No .txt files found in '{docs_dir}'.")

    for filename in txt_files:
        filepath = os.path.join(docs_dir, filename)
        professor_name = filename_to_professor_name(filename)

        with open(filepath, "r", encoding="utf-8") as f:
            raw_text = f.read()

        documents.append({
            "professor": professor_name,
            "filename": filename,
            "raw_text": raw_text,
        })
        print(f"  Loaded: {filename} → {professor_name}")

    return documents


def filename_to_professor_name(filename: str) -> str:
    """
    Converts filename to display name.
    'goel_apoorva.txt' → 'Apoorva Goel'
    'burns_tina.txt'   → 'Tina Burns'
    """
    base = filename.replace(".txt", "")
    parts = base.split("_")
    # Filename format is lastname_firstname, so reverse and title-case
    return " ".join(part.capitalize() for part in reversed(parts))


# ── Step 2: Clean raw text ────────────────────────────────────────────────────
def clean_text(raw_text: str) -> str:
    """
    Removes RMP boilerplate that isn't actual review content.
    Keeps: student review text, course codes, grade/difficulty mentions.
    Removes: star rating UI text, nav boilerplate, HTML entities, etc.
    """
    text = raw_text

    # Remove HTML entities
    text = text.replace("&amp;", "&")
    text = text.replace("&nbsp;", " ")
    text = text.replace("&#39;", "'")
    text = text.replace("&quot;", '"')
    text = text.replace("&lt;", "<")
    text = text.replace("&gt;", ">")

    # Remove any leftover HTML tags
    text = re.sub(r"<[^>]+>", "", text)

    # Remove RMP UI boilerplate lines (common patterns from copy-paste)
    boilerplate_patterns = [
        r"^Awesome \d.*$",
        r"^Great \d.*$",
        r"^Good \d.*$",
        r"^OK \d.*$",
        r"^Awful \d.*$",
        r"^RateCompare.*$",
        r"^I'm Professor.*$",
        r"^\d+% Would take again.*$",
        r"^Would take again.*$",
        r"^Level of Difficulty.*$",
        r"^Overall Quality.*$",
        r"^\d+ Student Ratings.*$",
        r"^All courses.*$",
        r"^Jump To Ratings.*$",
        r"^Professor in the.*department.*$",
        r"^Helpful\s*·.*$",
        r"^\d+\s*·\s*\d+\s*$",
        r"^For Credit:.*$",
        r"^Attendance:.*$",
        r"^Would Take Again:.*$",
        r"^Textbook:.*$",
        r"^Log In.*$",
        r"^Sign Up.*$",
    ]

    lines = text.split("\n")
    cleaned_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append("")  # preserve blank line separators
            continue
        # Skip lines matching boilerplate patterns
        if any(re.match(pattern, stripped, re.IGNORECASE) for pattern in boilerplate_patterns):
            continue
        cleaned_lines.append(stripped)

    # Collapse runs of 3+ blank lines into 2 (to preserve review separators)
    text = "\n".join(cleaned_lines)
    text = re.sub(r"\n{3,}", "\n\n", text)

    return text.strip()


# ── Step 3: Split into individual reviews ────────────────────────────────────
def split_into_reviews(cleaned_text: str) -> list[str]:
    """
    Splits cleaned text on blank lines.
    Each blank-line-separated block = one student review.
    Filters out empty or very short blocks (< 30 chars) that are likely artifacts.
    """
    blocks = cleaned_text.split("\n\n")
    reviews = []
    for block in blocks:
        block = block.strip()
        if len(block) >= 30:  # skip noise / stray single words
            reviews.append(block)
    return reviews


# ── Step 4: Chunk with fallback for long reviews ──────────────────────────────
def chunk_text(reviews: list[str], professor: str, filename: str) -> list[dict]:
    """
    Primary: 1 review = 1 chunk.
    Fallback: if a review exceeds MAX_CHUNK_CHARS, split with OVERLAP_CHARS overlap.
    Each chunk dict includes metadata: professor, source filename, chunk_index.
    """
    chunks = []
    chunk_index = 0

    for review in reviews:
        if len(review) <= MAX_CHUNK_CHARS:
            # Primary strategy: whole review is one chunk
            chunks.append({
                "text": review,
                "professor": professor,
                "source": filename,
                "chunk_index": chunk_index,
            })
            chunk_index += 1
        else:
            # Fallback: sliding window split
            sub_chunks = split_with_overlap(review, MAX_CHUNK_CHARS, OVERLAP_CHARS)
            for sub in sub_chunks:
                chunks.append({
                    "text": sub,
                    "professor": professor,
                    "source": filename,
                    "chunk_index": chunk_index,
                })
                chunk_index += 1

    return chunks


def split_with_overlap(text: str, max_chars: int, overlap: int) -> list[str]:
    """
    Splits a long string into sub-chunks of max_chars with overlap characters
    of context carried over from the previous chunk.
    """
    sub_chunks = []
    start = 0
    while start < len(text):
        end = start + max_chars
        sub_chunks.append(text[start:end])
        start += max_chars - overlap  # slide forward, keeping overlap
    return sub_chunks


# ── Step 5: Full pipeline ─────────────────────────────────────────────────────
def run_pipeline(docs_dir: str = DOCS_DIR) -> list[dict]:
    print(f"\n{'='*50}")
    print("STAGE 1: Loading documents")
    print(f"{'='*50}")
    documents = load_documents(docs_dir)
    print(f"\n✓ Loaded {len(documents)} documents\n")

    all_chunks = []

    print(f"{'='*50}")
    print("STAGE 2: Cleaning + Chunking")
    print(f"{'='*50}")

    for doc in documents:
        professor = doc["professor"]
        filename = doc["filename"]

        # Clean
        cleaned = clean_text(doc["raw_text"])

        # Split into individual reviews
        reviews = split_into_reviews(cleaned)

        # Chunk
        chunks = chunk_text(reviews, professor, filename)
        all_chunks.extend(chunks)

        print(f"  {professor}: {len(reviews)} reviews → {len(chunks)} chunks")

    print(f"\n✓ Total chunks: {len(all_chunks)}")

    # Validation check
    if len(all_chunks) < 50:
        print("⚠  WARNING: Fewer than 50 chunks — your reviews may not have loaded correctly,")
        print("   or reviews aren't separated by blank lines in your .txt files.")
    elif len(all_chunks) > 2000:
        print("⚠  WARNING: More than 2000 chunks — chunks may be too small.")
    else:
        print("✓ Chunk count looks healthy (50–2000 range)")

    return all_chunks


# ── Step 6: Inspect sample chunks ────────────────────────────────────────────
def inspect_chunks(chunks: list[dict], n: int = 5):
    """Prints n sample chunks for manual inspection."""
    import random
    print(f"\n{'='*50}")
    print(f"INSPECTION: {n} random chunks")
    print(f"{'='*50}")

    sample = random.sample(chunks, min(n, len(chunks)))
    for i, chunk in enumerate(sample, 1):
        print(f"\n--- Chunk {i} ---")
        print(f"Professor : {chunk['professor']}")
        print(f"Source    : {chunk['source']}")
        print(f"Length    : {len(chunk['text'])} chars")
        print(f"Text      : {chunk['text']}")
        print()


# ── Entry point ───────────────────────────────────────────────────────────────
if __name__ == "__main__":
    chunks = run_pipeline()
    inspect_chunks(chunks, n=5)

    # Save chunks to a simple JSON file for use in the next pipeline stage
    import json
    output_path = "chunks.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    print(f"\n✓ Chunks saved to '{output_path}' — ready for embedding stage")