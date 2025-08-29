import datetime
import os.path
import pickle

# NEW: Import the library to get the local timezone
from tzlocal import get_localzone

from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Define the scope. If modifying these scopes, delete the file token.pickle.
# 'readonly' provides read-only access.
# '.../auth/calendar' provides read/write access.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def get_calendar_service():
    """
    Authenticates the user and returns a Google Calendar API service object.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)

    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            # This requires the 'credentials.json' file you downloaded earlier.
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    try:
        service = build('calendar', 'v3', credentials=creds)
        return service
    except HttpError as error:
        print(f'An error occurred while building the service: {error}')
        return None

def list_events(service, num_events=10):
    """
    Lists the next 'num_events' from the primary calendar.
    """
    try:
        now = datetime.datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
        print(f'Getting the upcoming {num_events} events')
        events_result = service.events().list(
            calendarId='primary', 
            timeMin=now,
            maxResults=num_events, 
            singleEvents=True,
            orderBy='startTime'
        ).execute()
        events = events_result.get('items', [])

        if not events:
            print('No upcoming events found.')
            return

        print("\n--- Upcoming Events ---")
        for event in events:
            start = event['start'].get('dateTime', event['start'].get('date'))
            print(f"Event ID: {event['id']}")
            print(f"Start: {start}")
            print(f"Summary: {event['summary']}\n")
        print("-----------------------\n")

    except HttpError as error:
        print(f'An error occurred: {error}')

def create_event(service):
    """
    Creates a new event on the primary calendar based on user input.
    """
    try:
        summary = input("Enter event title: ")
        location = input("Enter event location (optional): ")
        description = input("Enter event description (optional): ")
        
        start_time_str = input("Enter start time (YYYY-MM-DD HH:MM): ")
        end_time_str = input("Enter end time (YYYY-MM-DD HH:MM): ")

        # --- CODE CHANGED HERE ---
        # Use tzlocal to get the IANA timezone name (e.g., 'America/New_York')
        local_tz = get_localzone()
        
        # Create naive datetime objects first
        naive_start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M")
        naive_end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M")

        # Make the naive datetimes timezone-aware using .replace()
        start_time = naive_start_time.replace(tzinfo=local_tz)
        end_time = naive_end_time.replace(tzinfo=local_tz)

        event = {
            'summary': summary,
            'location': location,
            'description': description,
            'start': {
                'dateTime': start_time.isoformat(),
                'timeZone': str(local_tz), # This will now be a valid IANA name
            },
            'end': {
                'dateTime': end_time.isoformat(),
                'timeZone': str(local_tz), # This will now be a valid IANA name
            },
            # --- END OF CHANGES ---
            'reminders': {
                'useDefault': False,
                'overrides': [
                    {'method': 'email', 'minutes': 24 * 60},
                    {'method': 'popup', 'minutes': 10},
                ],
            },
        }

        created_event = service.events().insert(calendarId='primary', body=event).execute()
        print(f"Event created successfully! Link: {created_event.get('htmlLink')}")

    except HttpError as error:
        print(f'An error occurred: {error}')
    except ValueError:
        print("Invalid date/time format. Please use YYYY-MM-DD HH:MM.")


def delete_event(service):
    """
    Deletes an event from the primary calendar using its ID.
    """
    try:
        event_id = input("Enter the Event ID to delete (run 'list' to find IDs): ")
        if not event_id:
            print("Event ID cannot be empty.")
            return

        service.events().delete(calendarId='primary', eventId=event_id).execute()
        print(f"Event with ID '{event_id}' deleted successfully.")

    except HttpError as error:
        if error.resp.status == 404:
            print(f"Error: Event with ID '{event_id}' not found.")
        else:
            print(f'An error occurred: {error}')

def main():
    """
    Main function to run the calendar management script.
    """
    # First, install the required libraries:
    # pip install --upgrade google-api-python-client google-auth-httplib2 google-auth-oauthlib tzlocal
    
    service = get_calendar_service()
    if not service:
        print("Could not connect to Google Calendar.")
        return

    while True:
        print("\nWhat would you like to do?")
        print("1. List upcoming events")
        print("2. Add a new event")
        print("3. Delete an event")
        print("4. Exit")
        choice = input("Enter your choice (1/2/3/4): ")

        if choice == '1':
            list_events(service)
        elif choice == '2':
            create_event(service)
        elif choice == '3':
            delete_event(service)
        elif choice == '4':
            print("Exiting.")
            break
        else:
            print("Invalid choice. Please try again.")

if __name__ == '__main__':
    main()
