"""
Compact and refresh the local ChromaDB SQLite metadata store.

Run this only while the FastAPI server is stopped. It does not rebuild the HNSW
vector files; use src/qa/vectorizer.py for a full embedding rebuild.
"""
import argparse
import os
import sqlite3


PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DEFAULT_DB_PATH = os.path.join(PROJECT_ROOT, "data", "vector_store", "chroma.sqlite3")


def optimize(db_path: str, vacuum: bool = False):
    if not os.path.exists(db_path):
        raise FileNotFoundError(f"Chroma SQLite file not found: {db_path}")

    before_size = os.path.getsize(db_path)

    con = sqlite3.connect(db_path)
    try:
        cur = con.cursor()
        cur.execute("PRAGMA busy_timeout = 5000")

        try:
            cur.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        except sqlite3.DatabaseError:
            # Chroma may use a journal mode where WAL checkpoint is not relevant.
            pass

        cur.execute("PRAGMA optimize")

        free_before = cur.execute("PRAGMA freelist_count").fetchone()[0]
        pages_before = cur.execute("PRAGMA page_count").fetchone()[0]

        if vacuum:
            cur.execute("VACUUM")

        free_after = cur.execute("PRAGMA freelist_count").fetchone()[0]
        pages_after = cur.execute("PRAGMA page_count").fetchone()[0]
    finally:
        con.close()

    after_size = os.path.getsize(db_path)
    print(f"Chroma SQLite: {db_path}")
    print(f"Size: {before_size / 1024 / 1024:.2f} MB -> {after_size / 1024 / 1024:.2f} MB")
    print(f"Freelist pages: {free_before} -> {free_after}")
    print(f"Total pages: {pages_before} -> {pages_after}")
    if not vacuum:
        print("Tip: pass --vacuum while the server is stopped to compact free pages.")


def main():
    parser = argparse.ArgumentParser(description="Optimize ChromaDB SQLite metadata store.")
    parser.add_argument("--db", default=DEFAULT_DB_PATH, help="Path to chroma.sqlite3")
    parser.add_argument("--vacuum", action="store_true", help="Run VACUUM to reclaim free pages")
    args = parser.parse_args()
    optimize(args.db, args.vacuum)


if __name__ == "__main__":
    main()
