import sqlite3

DB_PATH = 'events.db'

def connect():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('CREATE TABLE IF NOT EXISTS events (id TEXT PRIMARY KEY, status TEXT NOT NULL)')
    conn.commit()
    return conn

def get_status(conn, event_id):
    row = conn.execute('SELECT status FROM events WHERE id=?', (event_id,)).fetchone()
    return row[0] if row else None

def save_status(conn, event_id, status):
    conn.execute('INSERT INTO events(id,status) VALUES (?,?) ON CONFLICT(id) DO UPDATE SET status=excluded.status', (event_id, status))
    conn.commit()
