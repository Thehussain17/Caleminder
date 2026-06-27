# firebase_db.py
import json
import uuid
import os
from datetime import datetime
from google.genai import types

import firebase_admin
from firebase_admin import credentials
from google.cloud import firestore as google_firestore


class UserDB:
    """
    --- FIREBASE DATABASE COMPONENT ---
    Handles all database operations for storing and retrieving
    user profiles, authentication tokens, and conversation sessions
    using Google Cloud Firestore.

    Drop-in replacement for the SQLite-based user_database.py.
    """

    def __init__(self):
        # Initialize Firebase only once (singleton pattern)
        if not firebase_admin._apps:
            # Support credentials via JSON string env var (for cloud deployments)
            creds_json_str = os.environ.get("FIREBASE_CREDENTIALS_JSON")
            if creds_json_str:
                creds_dict = json.loads(creds_json_str)
                cred = credentials.Certificate(creds_dict)
                firebase_admin.initialize_app(cred)
            else:
                cred_path = os.environ.get("FIREBASE_CREDENTIALS_PATH", "firebase_service_account.json")
                if os.path.exists(cred_path):
                    cred = credentials.Certificate(cred_path)
                    firebase_admin.initialize_app(cred)
                else:
                    # Fall back to Application Default Credentials (for Cloud Run, etc.)
                    firebase_admin.initialize_app()

        # Use firebase_admin's built-in Firestore client.
        # This correctly uses the initialized app's credentials without any
        # manual credential extraction (which breaks with ADC fallback).
        from firebase_admin import firestore as fb_firestore
        self.db = fb_firestore.client()

    # =========================================================================
    # USER MANAGEMENT
    # =========================================================================

    def save_user(self, user_info, credentials_json):
        """
        Saves or updates a user's basic info and OAuth credentials.
        user_info: dict with 'id', 'email', 'name', 'picture'
        credentials_json: JSON string of the OAuth credentials
        """
        user_id = str(user_info['id'])
        user_ref = self.db.collection('users').document(user_id)
        existing = user_ref.get()

        # Preserve existing profile data if the user already exists
        profile = {}
        if existing.exists:
            data = existing.to_dict()
            profile = data.get('profile', {})

        user_ref.set({
            'email': user_info.get('email'),
            'name': user_info.get('name'),
            'picture': user_info.get('picture'),
            'profile': profile,
            'credentials': credentials_json,
            'updated_at': google_firestore.SERVER_TIMESTAMP,
        }, merge=True)

    def get_user_credentials(self, user_id):
        """Returns the stored OAuth credentials JSON string for a user."""
        doc = self.db.collection('users').document(str(user_id)).get()
        if doc.exists:
            return doc.to_dict().get('credentials')
        return None

    def get_user_profile(self, user_id):
        """Returns the user's profile dict."""
        doc = self.db.collection('users').document(str(user_id)).get()
        if doc.exists:
            return doc.to_dict().get('profile', {})
        return {}

    def update_user_profile_data(self, user_id, profile_dict):
        """Updates just the profile field for a user."""
        self.db.collection('users').document(str(user_id)).update({
            'profile': profile_dict,
        })

    def save_user_profile(self, user_id, profile_data):
        """Saves/replaces the full profile for a user (legacy compatibility)."""
        self.update_user_profile_data(user_id, profile_data)

    def load_user_profile(self, user_id):
        """Alias for get_user_profile (legacy compatibility)."""
        return self.get_user_profile(user_id)

    # =========================================================================
    # CHAT SESSION MANAGEMENT
    # =========================================================================

    def create_chat_session(self, user_id, title="New Chat"):
        """Creates a new chat session and returns its ID."""
        session_id = str(uuid.uuid4())
        self.db.collection('chat_sessions').document(session_id).set({
            'user_id': str(user_id),
            'title': title,
            'created_at': google_firestore.SERVER_TIMESTAMP,
        })
        return session_id

    def get_user_sessions(self, user_id):
        """Returns all chat sessions for a user, most recent first."""
        sessions_ref = (
            self.db.collection('chat_sessions')
            .where('user_id', '==', str(user_id))
            .order_by('created_at', direction=google_firestore.Query.DESCENDING)
        )
        sessions = []
        for doc in sessions_ref.stream():
            data = doc.to_dict()
            data['id'] = doc.id
            # Convert Firestore timestamp to string for JSON serialization
            if data.get('created_at'):
                data['created_at'] = data['created_at'].isoformat()
            sessions.append(data)
        return sessions

    def get_session(self, session_id):
        """Returns a single chat session dict, or None."""
        doc = self.db.collection('chat_sessions').document(session_id).get()
        if doc.exists:
            data = doc.to_dict()
            data['id'] = doc.id
            if data.get('created_at'):
                data['created_at'] = data['created_at'].isoformat()
            return data
        return None

    def update_session_title(self, session_id, title):
        """Updates the title of a chat session."""
        self.db.collection('chat_sessions').document(session_id).update({
            'title': title,
        })

    def delete_session(self, session_id):
        """Deletes a chat session and its history."""
        self.db.collection('chat_history').document(session_id).delete()
        self.db.collection('chat_sessions').document(session_id).delete()

    # =========================================================================
    # CHAT HISTORY MANAGEMENT
    # =========================================================================

    def save_chat_history(self, session_id, history):
        """
        Serializes and saves genai Content objects to Firestore.
        """
        serializable_history = []
        for c in history:
            role = c.role
            parts = []
            for part in c.parts:
                if part.text:
                    parts.append({'text': part.text})
                elif part.file_data:
                    parts.append({'text': '[FILE UPLOADED]'})
                elif part.function_call:
                    parts.append({
                        'function_call': {
                            'name': part.function_call.name,
                            'args': dict(part.function_call.args),
                        }
                    })
                elif part.function_response:
                    parts.append({
                        'function_response': {
                            'name': part.function_response.name,
                            'response': part.function_response.response,
                        }
                    })
            serializable_history.append({'role': role, 'parts': parts})

        self.db.collection('chat_history').document(session_id).set({
            'history': json.dumps(serializable_history),
        })

    def save_conversation_history(self, user_id, history):
        """
        Legacy compatibility: saves conversation history keyed by user_id.
        Converts genai Content objects to serializable format.
        """
        serializable_history = [
            {'role': c.role, 'parts': [part.text for part in c.parts if part.text]}
            for c in history
        ]
        self.db.collection('conversations').document(str(user_id)).set({
            'history': json.dumps(serializable_history),
        })

    def load_chat_history(self, session_id):
        """Loads and reconstructs genai Content objects from Firestore."""
        doc = self.db.collection('chat_history').document(session_id).get()
        if not doc.exists:
            return []

        data = doc.to_dict()
        history_data = json.loads(data.get('history', '[]'))
        reconstructed = []

        for item in history_data:
            parts = []
            for p in item['parts']:
                if 'text' in p:
                    parts.append(types.Part(text=p['text']))
                elif 'function_call' in p:
                    parts.append(types.Part(
                        function_call=types.FunctionCall(
                            name=p['function_call']['name'],
                            args=p['function_call']['args'],
                        )
                    ))
                elif 'function_response' in p:
                    parts.append(types.Part(
                        function_response=types.FunctionResponse(
                            name=p['function_response']['name'],
                            response=p['function_response']['response'],
                        )
                    ))
            reconstructed.append(types.Content(role=item['role'], parts=parts))

        return reconstructed

    def load_conversation_history(self, user_id):
        """
        Legacy compatibility: loads conversation history keyed by user_id.
        """
        doc = self.db.collection('conversations').document(str(user_id)).get()
        if not doc.exists:
            return []

        data = doc.to_dict()
        history_data = json.loads(data.get('history', '[]'))
        reconstructed = [
            types.Content(
                role=item['role'],
                parts=[types.Part(text=p) for p in item['parts']],
            )
            for item in history_data
        ]
        return reconstructed
