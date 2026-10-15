import sqlite3
from datetime import datetime, timezone

conn = sqlite3.connect("nfe_data.db")
cursor = conn.cursor()

cursor.execute("""
CREATE TABLE IF NOT EXISTS nfe_data (
    order_id TEXT PRIMARY KEY,
    status TEXT NOT NULL DEFAULT 'pending',
    payload TEXT NOT NULL,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    nfe TEXT,
    error_message TEXT
)
""")

conn.commit()
conn.close()