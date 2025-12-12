import sqlite3
import json
import os
import time

DB_QUEUE = "booking_queue.db"

class BookingQueue:
    def __init__(self):
        self._init_db()

    def _init_db(self):
        conn = sqlite3.connect(DB_QUEUE)
        c = conn.cursor()
        c.execute('''CREATE TABLE IF NOT EXISTS queue
                     (id INTEGER PRIMARY KEY AUTOINCREMENT,
                      payload TEXT,
                      status TEXT DEFAULT 'pending',
                      timestamp REAL)''')
        conn.commit()
        conn.close()

    def enqueue(self, vehicle_id, slot, note=None):
        payload = json.dumps({
            "vehicle_id": vehicle_id,
            "slot": slot,
            "note": note
        })
        conn = sqlite3.connect(DB_QUEUE)
        c = conn.cursor()
        c.execute("INSERT INTO queue (payload, timestamp) VALUES (?, ?)", (payload, time.time()))
        conn.commit()
        conn.close()
        return True

    def dequeue(self):
        conn = sqlite3.connect(DB_QUEUE)
        c = conn.cursor()
        # Get oldest pending item
        c.execute("SELECT id, payload FROM queue WHERE status='pending' ORDER BY id ASC LIMIT 1")
        row = c.fetchone()
        
        if row:
            msg_id, payload_str = row
            # Mark as processing
            c.execute("UPDATE queue SET status='processing' WHERE id=?", (msg_id,))
            conn.commit()
            conn.close()
            return msg_id, json.loads(payload_str)
        
        conn.close()
        return None, None

    def mark_done(self, msg_id, status="completed"):
        conn = sqlite3.connect(DB_QUEUE)
        c = conn.cursor()
        c.execute("UPDATE queue SET status=? WHERE id=?", (status, msg_id))
        conn.commit()
        conn.close()
