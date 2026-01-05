import sqlite3
import os
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "whetstone.db")

class DatabaseManager:
    def __init__(self, db_path=DB_PATH):
        self.db_path = db_path
        self._logging_enabled = False
        self._init_db()

    def _init_db(self):
        """Initialize the database schema if it doesn't exist."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS interactions (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        persona_name TEXT,
                        user_query TEXT,
                        ai_response TEXT,
                        session_id TEXT,
                        meta TEXT
                    )
                ''')
                # Future: Add other tables here (e.g., user_profiles, achievements)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")

    @property
    def logging_enabled(self):
        return self._logging_enabled

    @logging_enabled.setter
    def logging_enabled(self, value: bool):
        self._logging_enabled = value
        logger.info(f"Database logging set to: {self._logging_enabled}")

    def log_interaction(self, persona_name, user_query, ai_response, session_id=None, meta=None):
        """
        Log a chat interaction to the database.
        ONLY works if logging_enabled is True.
        """
        if not self._logging_enabled:
            return

        try:
            timestamp = datetime.utcnow().isoformat()
            meta_json = json.dumps(meta) if meta else "{}"
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO interactions (timestamp, persona_name, user_query, ai_response, session_id, meta)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (timestamp, persona_name, user_query, ai_response, session_id, meta_json))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to log interaction: {e}")

    def get_history(self, limit=50):
        """Retrieve recent chat history (for debugging or future features)."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('SELECT * FROM interactions ORDER BY id DESC LIMIT ?', (limit,))
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            logger.error(f"Failed to retrieve history: {e}")
            return []
