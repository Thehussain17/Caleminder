# user_database.py
import sqlite3
import json
import os
from google.genai import types

class UserDB:
    """
    --- DATABASE COMPONENT ---
    Handles all low-level database operations for storing and retrieving
    user profiles and conversation histories using a simple SQLite file.
    """
    def __init__(self, db_path='user_data.db'):
        self.db_path = db_path
        # Ensure the directory for the database exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)) or '.', exist_ok=True)
        self._initialize_db()

    def _get_connection(self):
        return sqlite3.connect(self.db_path)

    def _initialize_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Table for user profiles (name, preferences, etc.)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    profile TEXT
                )
            ''')
            # Table for conversation history
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS conversations (
                    user_id TEXT PRIMARY KEY,
                    history TEXT
                )
            ''')
            conn.commit()

    def save_user_profile(self, user_id, profile_data):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO users (id, profile) VALUES (?, ?)',
                (user_id, json.dumps(profile_data))
            )
            conn.commit()

    def load_user_profile(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT profile FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return json.loads(row[0]) if row else {}

    def save_conversation_history(self, user_id, history):
        # Convert genai Content objects to a serializable format
        serializable_history = [
            {'role': c.role, 'parts': [part.text for part in c.parts if part.text]} 
            for c in history
        ]
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO conversations (user_id, history) VALUES (?, ?)',
                (user_id, json.dumps(serializable_history))
            )
            conn.commit()

    def load_conversation_history(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT history FROM conversations WHERE user_id = ?', (user_id,))
            row = cursor.fetchone()
            if not row:
                return []
            
            # Reconstruct Content objects from serialized data
            history_data = json.loads(row[0])
            reconstructed_history = [
                types.Content(role=item['role'], parts=[types.Part(text=p) for p in item['parts']])
                for item in history_data
            ]
            return reconstructed_history
