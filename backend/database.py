import sqlite3, json, os
from dotenv import load_dotenv
load_dotenv()

DB_PATH = os.getenv("DB_PATH", "./chats.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id TEXT PRIMARY KEY,
            name TEXT,
            summary TEXT DEFAULT '',
            pinned_memory TEXT DEFAULT '[]',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            chat_id TEXT,
            role TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(chat_id) REFERENCES chats(id)
        )
    """)
    conn.commit()
    conn.close()

def create_chat(chat_id: str, name: str):
    conn = get_conn()
    conn.execute("INSERT INTO chats (id, name) VALUES (?, ?)", (chat_id, name))
    conn.commit()
    conn.close()

def get_all_chats():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM chats ORDER BY created_at DESC").fetchall()
    conn.close()
    return [dict(r) for r in rows]

def get_chat(chat_id: str):
    conn = get_conn()
    row = conn.execute("SELECT * FROM chats WHERE id=?", (chat_id,)).fetchone()
    conn.close()
    return dict(row) if row else None

def rename_chat(chat_id: str, name: str):
    conn = get_conn()
    conn.execute("UPDATE chats SET name=? WHERE id=?", (name, chat_id))
    conn.commit()
    conn.close()

def delete_chat(chat_id: str):
    conn = get_conn()
    conn.execute("DELETE FROM messages WHERE chat_id=?", (chat_id,))
    conn.execute("DELETE FROM chats WHERE id=?", (chat_id,))
    conn.commit()
    conn.close()

def add_message(chat_id: str, role: str, content: str):
    conn = get_conn()
    conn.execute("INSERT INTO messages (chat_id, role, content) VALUES (?,?,?)",
                 (chat_id, role, content))
    conn.commit()
    conn.close()

def get_messages(chat_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT role, content FROM messages WHERE chat_id=? ORDER BY id ASC",
        (chat_id,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]

def update_summary(chat_id: str, summary: str):
    conn = get_conn()
    conn.execute("UPDATE chats SET summary=? WHERE id=?", (summary, chat_id))
    conn.commit()
    conn.close()

def update_pinned(chat_id: str, pinned: list):
    conn = get_conn()
    conn.execute("UPDATE chats SET pinned_memory=? WHERE id=?",
                 (json.dumps(pinned), chat_id))
    conn.commit()
    conn.close()

def get_message_count(chat_id: str):
    conn = get_conn()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM messages WHERE chat_id=?", (chat_id,)
    ).fetchone()
    conn.close()
    return row["cnt"]
