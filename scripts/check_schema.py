import sqlite3

db_path = "./data/turkish_recipes_db/chroma.sqlite3"
try:
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute("PRAGMA table_info(embeddings)")
    columns = cursor.fetchall()
    for col in columns:
        print(col)
except Exception as e:
    print(f"Error: {e}")
