"""
Step 1: Document Chunker + ChromaDB Vectorizer
───────────────────────────────────────────────
Reads the Camstar PDF, splits into ~500-char chunks by chapter,
embeds with sentence-transformers, stores in ChromaDB.
"""
import os
import re
import fitz  # PyMuPDF
import chromadb
from chromadb.utils.embedding_functions import SentenceTransformerEmbeddingFunction
from dotenv import load_dotenv

load_dotenv()

CHUNK_SIZE = 500       # characters per chunk
CHUNK_OVERLAP = 80     # overlap between chunks
COLLECTION_NAME = "camstar_docs"
PERSIST_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "data", "vector_store")
EMBEDDING_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"


def extract_chapters(pdf_path: str) -> list[dict]:
    """Extract text from PDF, grouped by chapter."""
    doc = fitz.open(pdf_path)
    toc = doc.get_toc()

    # Build chapter ranges from TOC level-1 entries
    chapters = []
    level1_entries = [(title, page - 1) for level, title, page in toc if level == 1]

    for i, (title, start_page) in enumerate(level1_entries):
        end_page = level1_entries[i + 1][1] if i + 1 < len(level1_entries) else len(doc)
        text = ""
        for pg in range(start_page, min(end_page, len(doc))):
            page_text = doc[pg].get_text()
            # Remove excessive whitespace
            page_text = re.sub(r'\n{3,}', '\n\n', page_text)
            text += page_text
        if text.strip():
            chapters.append({"title": title, "start_page": start_page + 1, "text": text.strip()})

    doc.close()
    return chapters


def chunk_text(text: str, title: str, start_page: int) -> list[dict]:
    """Split text into overlapping chunks with metadata."""
    chunks = []
    pos = 0
    idx = 0
    while pos < len(text):
        end = pos + CHUNK_SIZE
        chunk_text_slice = text[pos:end]

        # Try to break at sentence boundary
        if end < len(text):
            last_period = max(
                chunk_text_slice.rfind('。'),
                chunk_text_slice.rfind('. '),
                chunk_text_slice.rfind('\n\n'),
            )
            if last_period > CHUNK_SIZE * 0.3:
                end = pos + last_period + 1
                chunk_text_slice = text[pos:end]

        if chunk_text_slice.strip():
            chunks.append({
                "id": f"{title[:30]}_{idx}",
                "text": chunk_text_slice.strip(),
                "metadata": {
                    "chapter": title,
                    "start_page": start_page,
                    "chunk_index": idx,
                }
            })
            idx += 1

        pos = end - CHUNK_OVERLAP if end < len(text) else len(text)

    return chunks


def build_vector_store(pdf_path: str):
    """Main entry: extract → chunk → embed → store."""
    print(f"[Step 1] Extracting chapters from {pdf_path}...")
    chapters = extract_chapters(pdf_path)
    print(f"  Found {len(chapters)} chapters")

    all_chunks = []
    for ch in chapters:
        ch_chunks = chunk_text(ch["text"], ch["title"], ch["start_page"])
        all_chunks.extend(ch_chunks)
    print(f"  Total chunks: {len(all_chunks)}")

    # Initialize ChromaDB with persistence
    os.makedirs(PERSIST_DIR, exist_ok=True)
    print(f"[Step 1] Loading embedding model: {EMBEDDING_MODEL} (first run downloads ~400MB)...")
    embed_fn = SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL,
        device="cpu",
    )

    client = chromadb.PersistentClient(path=PERSIST_DIR)

    # Delete existing collection if any
    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
        metadata={"hnsw:space": "cosine"},
    )

    # Batch insert
    BATCH = 100
    for i in range(0, len(all_chunks), BATCH):
        batch = all_chunks[i:i + BATCH]
        collection.add(
            ids=[c["id"] for c in batch],
            documents=[c["text"] for c in batch],
            metadatas=[c["metadata"] for c in batch],
        )
        print(f"  Inserted batch {i // BATCH + 1}/{(len(all_chunks) - 1) // BATCH + 1}")

    print(f"[Step 1] Vector store built: {collection.count()} chunks in {PERSIST_DIR}")
    return collection


def get_vector_collection():
    """Get an existing ChromaDB collection for querying."""
    embed_fn = SentenceTransformerEmbeddingFunction(
        model_name=EMBEDDING_MODEL,
        device="cpu",
    )
    client = chromadb.PersistentClient(path=PERSIST_DIR)
    return client.get_collection(
        name=COLLECTION_NAME,
        embedding_function=embed_fn,
    )


if __name__ == "__main__":
    pdf = os.path.join(os.path.dirname(__file__), "..", "..", "docs", "OCEXCR_Modeling_2510plus_R1.pdf")
    if os.path.exists(pdf):
        build_vector_store(pdf)
    else:
        print(f"PDF not found: {pdf}")
