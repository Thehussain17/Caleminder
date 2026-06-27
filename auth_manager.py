# auth_manager.py
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from google.auth.transport.requests import Request
import os
import pickle

class AuthManager:
    def __init__(self):
        self.scopes = [
            'https://www.googleapis.com/auth/calendar',
            'https://www.googleapis.com/auth/tasks',
            'https://www.googleapis.com/auth/contacts.readonly',
            'https://www.googleapis.com/auth/gmail.send',
            'https://www.googleapis.com/auth/drive'
        ]
        self.token_dir = 'user_tokens'
        if not os.path.exists(self.token_dir):
            os.makedirs(self.token_dir)
        
        # --- NEW: Define the redirect URI ---
        # This MUST match what you entered in the Google Cloud Console.
        self.redirect_uri = 'http://127.0.0.1:5000/oauth2callback'

    def _get_token_path(self, user_id):
        return os.path.join(self.token_dir, f'token_{user_id}.pickle')

    def get_credentials(self, user_id):
        token_path = self._get_token_path(user_id)
        creds = None
        if os.path.exists(token_path):
            with open(token_path, 'rb') as token:
                creds = pickle.load(token)
        
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
        
        return creds if creds and creds.valid else None

    def get_authorization_url(self, user_id):
        """
        Generates a stateful authorization URL. The 'state' parameter will
        be passed back to our callback, so we know which user is authorizing.
        """
        flow = Flow.from_client_secrets_file('credentials.json', self.scopes)
        flow.redirect_uri = self.redirect_uri
        auth_url, state = flow.authorization_url(
            access_type='offline',
            prompt='consent',
            state=str(user_id) # Pass the user_id as the state
        )
        return auth_url

    def exchange_code_for_credentials(self, code, state):
        """
        Exchanges the authorization code from the web callback for credentials.
        The 'state' is the user_id we passed in the URL.
        """
        user_id = str(state)
        flow = Flow.from_client_secrets_file('credentials.json', self.scopes)
        flow.redirect_uri = self.redirect_uri
        
        try:
            flow.fetch_token(code=code)
            creds = flow.credentials
            token_path = self._get_token_path(user_id)
            with open(token_path, 'wb') as token:
                pickle.dump(creds, token)
            return True, "Authorization successful! You can now close this page and return to Telegram."
        except Exception as e:
            print(f"Error exchanging code for user {user_id}: {e}")
            return False, "Authorization failed. Please try again."

