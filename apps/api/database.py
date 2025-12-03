import sqlite3
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Optional, Any

DB_PATH = Path("audio2txt.db")

class DatabaseManager:
    def __init__(self):
        self.conn = sqlite3.connect(DB_PATH, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_db()

    def _init_db(self):
        """Initialize database schema"""
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                status TEXT,
                progress INTEGER,
                template_id TEXT,
                file_path TEXT,
                created_at TIMESTAMP,
                completed_at TIMESTAMP,
                result_json TEXT,
                error_message TEXT
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS vocabulary (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                word TEXT NOT NULL UNIQUE,
                category TEXT,
                created_at TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_vocabulary(self, word: str, category: str = "general"):
        cursor = self.conn.cursor()
        try:
            cursor.execute("INSERT INTO vocabulary (word, category, created_at) VALUES (?, ?, ?)", 
                          (word, category, datetime.now()))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def get_vocabulary(self) -> List[str]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT word FROM vocabulary")
        return [row["word"] for row in cursor.fetchall()]

    def delete_vocabulary(self, word: str):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM vocabulary WHERE word = ?", (word,))
        self.conn.commit()

    def create_task(self, task_id: str, file_path: str, template_id: str):
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO tasks (id, status, progress, file_path, template_id, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (task_id, "pending", 0, file_path, template_id, datetime.now()))
        self.conn.commit()

    def update_task(self, task_id: str, status: str, progress: int, result: Optional[Dict] = None, error: Optional[str] = None):
        cursor = self.conn.cursor()
        update_fields = ["status = ?", "progress = ?"]
        params = [status, progress]

        if result:
            update_fields.append("result_json = ?")
            params.append(json.dumps(result))
            update_fields.append("completed_at = ?")
            params.append(datetime.now())
        
        if error:
            update_fields.append("error_message = ?")
            params.append(error)

        params.append(task_id)
        
        sql = f"UPDATE tasks SET {', '.join(update_fields)} WHERE id = ?"
        cursor.execute(sql, params)
        self.conn.commit()

    def get_task(self, task_id: str) -> Optional[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row:
            return self._row_to_dict(row)
        return None

    def get_all_tasks(self, limit: int = 50) -> List[Dict]:
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks ORDER BY created_at DESC LIMIT ?", (limit,))
        return [self._row_to_dict(row) for row in cursor.fetchall()]

    def _row_to_dict(self, row) -> Dict:
        d = dict(row)
        if d.get("result_json"):
            d["result"] = json.loads(d["result_json"])
        return d

db = DatabaseManager()
