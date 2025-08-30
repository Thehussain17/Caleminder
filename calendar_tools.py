# calendar_tools.py
import os
import pickle
import json
import datetime
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as date_parse
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tzlocal import get_localzone

SCOPES = ['https://www.googleapis.com/auth/calendar','https://www.googleapis.com/auth/tasks']

class GoogleCalendarTools:
    def __init__(self):
        self.service = self._get_calendar_service()
        if not self.service:
            raise ConnectionError("Failed to connect to Google Calendar. Check credentials.json.")

    def _get_calendar_service(self):
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    raise FileNotFoundError("FATAL ERROR: credentials.json not found.")
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.pickle', 'wb') as token:
                pickle.dump(creds, token)
        return build('calendar', 'v3', credentials=creds)

    def create_event(self, summary: str, start_time_str: str, end_time_str: str, description: str = "", location: str = "", color_id: str = None) -> dict:
        """
        Creates a new event on the user's primary calendar, with an optional color.
        """
        local_tz = get_localzone()
        try:
            start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
            end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
            event_body = {
                'summary': summary, 'location': location, 'description': description,
                'start': {'dateTime': start_time.isoformat(), 'timeZone': str(local_tz)},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': str(local_tz)},
            }
            # --- NEW: Add colorId to the event if provided ---
            if color_id:
                event_body['colorId'] = color_id
            
            created_event = self.service.events().insert(calendarId='primary', body=event_body).execute()
            return {"status": "success", "message": f"Event '{created_event['summary']}' was created."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
        
    def get_now(self) -> dict:
        """
        Returns the current date and time.
        This is useful for resolving queries like 'schedule a meeting for today'.
        """
        # --- FIX: Return a dictionary, as required by the SDK's FunctionResponse ---
        return {"current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}

    def list_events(self, max_results: int = 10) -> dict:
        """
        Lists the next 'max_results' events on the user's primary calendar.
        """
        try:
            now = datetime.datetime.utcnow().isoformat() + 'Z'
            events_result = self.service.events().list(calendarId='primary', timeMin=now,
                                                       maxResults=max_results, singleEvents=True,
                                                       orderBy='startTime').execute()
            events = events_result.get('items', [])
            if not events:
                return {"status": "success", "events": []}
            event_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                event_list.append({'summary': event['summary'], 'start': start})
            return {"status": "success", "events": event_list}
        except HttpError as error:
            return {"status": "error", "message": f"An error occurred: {error}"}   
        
    def remove_event(self, event_id: str) -> dict:
        """
        Removes an event from the user's primary calendar by event ID.
        """
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return {"status": "success", "message": f"Event with ID '{event_id}' was removed."}
        except HttpError as error:
            return {"status": "error", "message": f"An error occurred: {error}"}

    # In calendar_tools.py

    def schedule_timetable(self, events: list) -> dict:

        """Schedules multiple events on the user's primary calendar."""
        successful_events = 0
        failed_events = 0
        for event_data in events:
            try:
                self.create_event(**event_data)
                successful_events += 1
            except Exception as e:
                print(f"Failed to schedule event: {event_data} - {e}")
                failed_events += 1

        return {
        "status": "complete",
        "message": f"Successfully scheduled {successful_events} events. {failed_events} events failed."
    }


    def get_events_by_date(self, date_str: str) -> dict:
        """
        Retrieves all events on a specific date.
        Args:
            date_str: The date to fetch events for, in "YYYY-MM-DD" format.
        """
        try:
            local_tz = get_localzone()
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            start_of_day = datetime.datetime.combine(date, datetime.time.min, tzinfo=local_tz)
            end_of_day = datetime.datetime.combine(date, datetime.time.max, tzinfo=local_tz)

            events_result = self.service.events().list(
                calendarId='primary', 
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(), 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            if not events:
                return {"status": "success", "events": []}
            
            event_list = []
            for event in events:
                start = event['start'].get('dateTime', event['start'].get('date'))
                event_list.append({'summary': event['summary'], 'start': start})
            
            return {"status": "success", "events": event_list}
        except Exception as e:
            return {"status": "error", "message": str(e)}  
        
    def get_events(self, start_date_query: str, end_date_query: str = None) -> dict:
        """
        Retrieves all events for a given date or date range.
        Handles queries like 'today', 'tomorrow', 'next week', 'August 30th'.
        Args:
            start_date_query: The start date of the range (e.g., 'today', 'next Monday').
            end_date_query: The optional end date of the range (e.g., 'next Sunday'). If omitted, events for a single day are fetched.
        """
        try:
            start_date = date_parse(start_date_query).date()
            
            # If an end date is provided, parse it. Otherwise, it's the same as the start date.
            if end_date_query:
                end_date = date_parse(end_date_query).date()
            else:
                end_date = start_date

            local_tz = get_localzone()
            start_of_range = datetime.datetime.combine(start_date, datetime.time.min, tzinfo=local_tz)
            end_of_range = datetime.datetime.combine(end_date, datetime.time.max, tzinfo=local_tz)

            events_result = self.service.events().list(
                calendarId='primary', 
                timeMin=start_of_range.isoformat(),
                timeMax=end_of_range.isoformat(), 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            if not events:
                return {"status": "success", "events": [], "message": f"No events found between {start_date.strftime('%Y-%m-%d')} and {end_date.strftime('%Y-%m-%d')}."}
            
            event_list = [{'summary': event['summary'], 'start': event['start'].get('dateTime', event['start'].get('date'))} for event in events]
            
            return {"status": "success", "events": event_list}
        except Exception as e:
            return {"status": "error", "message": f"Could not process date query. Please be more specific. Error: {str(e)}"}
        
    def find_event_id(self, summary: str, date_str: str) -> dict:
        """
        Finds the event ID for an event with a given summary on a specific date.
        Args:
            summary: The summary (title) of the event to search for.
            date_str: The date to search on, in "YYYY-MM-DD" format.
        """
        try:
            local_tz = get_localzone()
            date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
            start_of_day = datetime.datetime.combine(date, datetime.time.min, tzinfo=local_tz)
            end_of_day = datetime.datetime.combine(date, datetime.time.max, tzinfo=local_tz)

            events_result = self.service.events().list(
                calendarId='primary', 
                timeMin=start_of_day.isoformat(),
                timeMax=end_of_day.isoformat(), 
                singleEvents=True,
                orderBy='startTime'
            ).execute()
            
            events = events_result.get('items', [])
            for event in events:
                if event['summary'].lower() == summary.lower():
                    return {"status": "success", "event_id": event['id']}
            
            return {"status": "error", "message": f"No event found with summary '{summary}' on {date_str}."}
        except Exception as e:
            return {"status": "error", "message": str(e)}