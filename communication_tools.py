# communication_tools.py
import os.path
import pickle
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the scopes for all required services
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/contacts', # Read contacts
    'https://www.googleapis.com/auth/gmail.send'       # Send emails
]

class CommunicationTools:
    def __init__(self):
        creds = self._get_credentials()
        self.people_service = build('people', 'v1', credentials=creds)
        self.gmail_service = build('gmail', 'v1', credentials=creds)

    def _get_credentials(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            # Check if token exists and has all required scopes
            has_all_scopes = all(s in creds.scopes for s in SCOPES) if creds else False
            if creds and creds.expired and creds.refresh_token and has_all_scopes:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return creds

    def find_contact(self, name_query: str) -> dict:
        """
        Finds a contact by name and returns their email address.
        Handles cases where no contact is found, or contacts are found but have no email.
        """
        try:
            # --- FIX: Use the correct 'searchContacts' method for querying ---
            results = self.people_service.people().searchContacts(
                query=name_query,
                pageSize=5,
                readMask='names,emailAddresses'
            ).execute()
            
            # The response structure is different for searchContacts
            search_results = results.get('results', [])
            connections = [result.get('person') for result in search_results if result.get('person')]


            # Case 1: No contacts found at all matching the query.
            if not connections:
                return {"status": "not_found", "message": f"No contact found matching '{name_query}'."}

            # Filter the found connections to only include those with email addresses.
            contacts_with_email = []
            for person in connections:
                names = person.get('names', [{}])
                emails = person.get('emailAddresses', []) # Email is a list, not a dict with a value
                
                # We only care about contacts that have a name and at least one email.
                if names and emails:
                    contacts_with_email.append({
                        "name": names[0].get('displayName', 'N/A'),
                        "email": emails[0].get('value')
                    })
            
            # Case 2: Contacts were found, but none of them have an email address listed.
            if not contacts_with_email:
                return {
                    "status": "no_email_found", 
                    "message": f"Found contacts matching '{name_query}', but none have an email address."
                }

            # Case 3: Success! We found one or more contacts with email addresses.
            return {"status": "success", "contacts": contacts_with_email}

        except HttpError as e:
            # Handle potential API errors (e.g., permissions issues)
            return {"status": "error", "message": f"An API error occurred while searching for contacts: {e}"}

    def send_email(self, to: str, subject: str, body: str) -> dict:
        """Sends an email to a specified recipient."""
        try:
            message = MIMEText(body)
            message['to'] = to
            message['subject'] = subject
            encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()

            create_message = {'raw': encoded_message}
            send_message = self.gmail_service.users().messages().send(userId='me', body=create_message).execute()
            return {"status": "success", "message": f"Email sent successfully to {to}."}
        except HttpError as error:
            return {"status": "error", "message": f"An error occurred: {error}"}
