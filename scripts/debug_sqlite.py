import sqlite3

db_path = "./data/turkish_recipes_db/chroma.sqlite3"
print(f"Connecting to SQLite at {db_path}...")

try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    print("Tables:", [t[0] for t in tables])
    
    # Let's try to count total documents
    # In newer Chroma (0.4+), embeddings and documents are linked.
    # The table might be called 'embeddings' or 'embedding_fulltext'.
    if ('embeddings',) in tables:
        cursor.execute("SELECT COUNT(*) FROM embeddings")
        print("Embeddings count:", cursor.fetchone()[0])
    
    if ('collections',) in tables:
        cursor.execute("SELECT id, name FROM collections")
        print("Collections:", cursor.fetchall())

    print("\nSUCCESS: SQLite is readable.")

except Exception as e:
    print("\nFAILURE!")
    print(f"Error: {e}")
