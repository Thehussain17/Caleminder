# user_database.py
import sqlite3
import json
import os
import uuid
from datetime import datetime
from google.genai import types

class UserDB:
    """
    --- DATABASE COMPONENT ---
    Handles all low-level database operations for storing and retrieving
    user profiles, authentication tokens, and conversation sessions.
    """
    def __init__(self, db_path='user_data.db'):
        self.db_path = db_path
        # Ensure the directory for the database exists
        os.makedirs(os.path.dirname(os.path.abspath(db_path)) or '.', exist_ok=True)
        self._initialize_db()

    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _initialize_db(self):
        with self._get_connection() as conn:
            cursor = conn.cursor()

            # Users table: Stores profile and OAuth credentials
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT,
                    name TEXT,
                    picture TEXT,
                    profile TEXT,
                    credentials TEXT
                )
            ''')

            # Chat Sessions table: Manages multiple chats per user
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    user_id TEXT,
                    title TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY(user_id) REFERENCES users(id)
                )
            ''')

            # Chat History table: Stores the actual conversation content for a session
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS chat_history (
                    session_id TEXT PRIMARY KEY,
                    history TEXT,
                    FOREIGN KEY(session_id) REFERENCES chat_sessions(id)
                )
            ''')
            conn.commit()

    # --- USER MANAGEMENT ---

    def save_user(self, user_info, credentials_json):
        """
        Saves or updates a user's basic info and credentials.
        user_info: dict containing 'id' (sub), 'email', 'name', 'picture'
        credentials_json: JSON string of the OAuth credentials
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            # Check if user exists to preserve existing profile data
            cursor.execute('SELECT profile FROM users WHERE id = ?', (user_info['id'],))
            existing_user = cursor.fetchone()
            profile = existing_user['profile'] if existing_user else '{}'

            cursor.execute('''
                INSERT OR REPLACE INTO users (id, email, name, picture, profile, credentials)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_info['id'],
                user_info.get('email'),
                user_info.get('name'),
                user_info.get('picture'),
                profile,
                credentials_json
            ))
            conn.commit()

    def update_user_profile_data(self, user_id, profile_dict):
        """
        Updates just the profile JSON blob for a user.
        """
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'UPDATE users SET profile = ? WHERE id = ?',
                (json.dumps(profile_dict), user_id)
            )
            conn.commit()

    def get_user_credentials(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT credentials FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return row['credentials'] if row else None

    def get_user_profile(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT profile FROM users WHERE id = ?', (user_id,))
            row = cursor.fetchone()
            return json.loads(row['profile']) if row else {}

    # --- CHAT SESSION MANAGEMENT ---

    def create_chat_session(self, user_id, title="New Chat"):
        session_id = str(uuid.uuid4())
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT INTO chat_sessions (id, user_id, title) VALUES (?, ?, ?)',
                (session_id, user_id, title)
            )
            conn.commit()
        return session_id

    def get_user_sessions(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC',
                (user_id,)
            )
            return [dict(row) for row in cursor.fetchall()]

    def get_session(self, session_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT * FROM chat_sessions WHERE id = ?', (session_id,))
            row = cursor.fetchone()
            return dict(row) if row else None

    def update_session_title(self, session_id, title):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('UPDATE chat_sessions SET title = ? WHERE id = ?', (title, session_id))
            conn.commit()

    def delete_session(self, session_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('DELETE FROM chat_history WHERE session_id = ?', (session_id,))
            cursor.execute('DELETE FROM chat_sessions WHERE id = ?', (session_id,))
            conn.commit()

    # --- CHAT HISTORY MANAGEMENT ---

    def save_chat_history(self, session_id, history):
        # Convert genai Content objects to a serializable format
        serializable_history = []
        for c in history:
            role = c.role
            parts = []
            for part in c.parts:
                if part.text:
                    parts.append({'text': part.text})
                elif part.file_data:
                     # We don't store file data blobs, just a placeholder or reference if needed
                     # For now, we assume transient file uploads or store a marker
                     parts.append({'text': '[FILE UPLOADED]'})
                elif part.function_call:
                     parts.append({'function_call': {'name': part.function_call.name, 'args': dict(part.function_call.args)}})
                elif part.function_response:
                     parts.append({'function_response': {'name': part.function_response.name, 'response': part.function_response.response}})

            serializable_history.append({'role': role, 'parts': parts})

        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                'INSERT OR REPLACE INTO chat_history (session_id, history) VALUES (?, ?)',
                (session_id, json.dumps(serializable_history))
            )
            conn.commit()

    def load_chat_history(self, session_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT history FROM chat_history WHERE session_id = ?', (session_id,))
            row = cursor.fetchone()
            if not row:
                return []
            
            # Reconstruct Content objects from serialized data
            history_data = json.loads(row['history'])
            reconstructed_history = []

            for item in history_data:
                parts = []
                for p in item['parts']:
                    if 'text' in p:
                        parts.append(types.Part(text=p['text']))
                    elif 'function_call' in p:
                        parts.append(types.Part(function_call=types.FunctionCall(name=p['function_call']['name'], args=p['function_call']['args'])))
                    elif 'function_response' in p:
                         parts.append(types.Part(function_response=types.FunctionResponse(name=p['function_response']['name'], response=p['function_response']['response'])))

                reconstructed_history.append(types.Content(role=item['role'], parts=parts))

            return reconstructed_history
