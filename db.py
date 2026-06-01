import sqlite3, os
from dotenv import load_dotenv
load_dotenv()
DB_PATH = os.getenv("DB_PATH", "gatekeeper.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            agent_id TEXT, agent_name TEXT,
            requested_scope TEXT, approved_scope TEXT,
            approved_by TEXT, status TEXT DEFAULT 'pending',
            started_at TEXT, exited_at TEXT
        );
        CREATE TABLE IF NOT EXISTS access_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT, resource TEXT, action TEXT,
            allowed INTEGER, reason TEXT, timestamp TEXT
        );
    """)
    conn.commit()
    conn.close()
