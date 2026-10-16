import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parent / "nfe_data.db"

def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS nfe_data (
                order_id TEXT PRIMARY KEY,
                status TEXT NOT NULL DEFAULT 'pending',
                payload TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                nfe TEXT,
                error_message TEXT,
                package_count INTEGER NOT NULL DEFAULT 1,
                should_emit INTEGER NOT NULL DEFAULT 1
            )
        """)

    print(f"Banco inicializado em: {DB_PATH}")

if __name__ == "__main__":
    init_db()
