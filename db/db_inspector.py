import sqlite3
import os

# go up one directory from /db/ to project root
DB_PATH = os.path.join(os.path.dirname(__file__), "..", "data", "warehouse.db")

def inspect_db(db_path=DB_PATH):
    con = sqlite3.connect(db_path)
    cur = con.cursor()

    print(f"📂 Connected to: {db_path}")

    # List all tables
    print("\n📂 Tables in DB:")
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cur.fetchall()
    for t in tables:
        print(" -", t[0])

    print("\n📑 Columns in each table:")
    for t in tables:
        table_name = t[0]
        cur.execute(f"PRAGMA table_info({table_name});")
        cols = cur.fetchall()
        col_names = [c[1] for c in cols]
        print(f" - {table_name}: {col_names}")

    con.close()

if __name__ == "__main__":
    inspect_db()
