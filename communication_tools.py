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
        """Finds a contact by name and returns their email address."""
        try:
            results = self.people_service.people().connections().list(
                resourceName='people/me',
                pageSize=5,
                personFields='names,emailAddresses',
                query=name_query
            ).execute()
            connections = results.get('connections', [])

            if not connections:
                return {"status": "not_found", "message": f"No contact found matching '{name_query}'."}
            
            contact_list = []
            for person in connections:
                names = person.get('names', [{}])
                emails = person.get('emailAddresses', [{}])
                if emails:
                    contact_list.append({
                        "name": names[0].get('displayName'),
                        "email": emails[0].get('value')
                    })
            return {"status": "success", "contacts": contact_list}
        except HttpError as e:
            return {"status": "error", "message": f"An API error occurred: {e}"}

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
