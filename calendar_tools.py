# calendar_tools.py
import os
import pickle
import json
import datetime
import uuid
from dateutil.relativedelta import relativedelta
from dateutil.parser import parse as date_parse
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from tzlocal import get_localzone

class GoogleCalendarTools:
    def __init__(self, credentials_data=None):
        """
        initializes the calendar tools.
        credentials_data: A dictionary or JSON string containing the OAuth 2.0 credentials
                          (token, refresh_token, token_uri, client_id, client_secret, scopes).
        """
        self.service = None
        if credentials_data:
            self.authenticate(credentials_data)

    def authenticate(self, credentials_data):
        """
        Authenticates the user using provided credentials data.
        """
        try:
            if isinstance(credentials_data, str):
                credentials_data = json.loads(credentials_data)

            creds = Credentials.from_authorized_user_info(credentials_data)

            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())

            self.service = build('calendar', 'v3', credentials=creds)
            return True
        except Exception as e:
            print(f"Authentication failed: {e}")
            self.service = None
            return False

    def _check_service(self):
        if not self.service:
            return {"status": "error", "message": "User is not authenticated. Please log in."}
        return None

    def create_event(self, summary: str, start_time_str: str, end_time_str: str, description: str = "", location: str = "", event_type: str = "personal", recurrence_freq: str = None, recurrence_until: str = None, create_meet_link: bool = False) -> dict:
        """
        Creates a new event, applying a specific color based on the event's category (event_type).
        """
        if err := self._check_service(): return err

        local_tz = get_localzone()

        # Maps the conceptual event_type to a specific Google Calendar color ID.
        event_type_to_color = {
            "work": "8",       # Graphite
            "personal": "2",   # Sage
            "focus_time": "9", # Blueberry
            "health": "4",     # Flamingo
            "social": "6",     # Tangerine
            "urgent": "11"     # Tomato
        }

        try:
            start_time = datetime.datetime.strptime(start_time_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)
            end_time = datetime.datetime.strptime(end_time_str, "%Y-%m-%d %H:%M").replace(tzinfo=local_tz)

            event_body = {
                'summary': summary,
                'location': location,
                'description': description,
                'start': {'dateTime': start_time.isoformat(), 'timeZone': str(local_tz)},
                'end': {'dateTime': end_time.isoformat(), 'timeZone': str(local_tz)},
                'colorId': event_type_to_color.get(event_type.lower(), "2") # Default to Sage
            }

            insert_kwargs = {'calendarId': 'primary', 'body': event_body}

            if create_meet_link:
                event_body['conferenceData'] = {
                    'createRequest': {
                        'requestId': f"{uuid.uuid4().hex}",
                        'conferenceSolutionKey': {'type': 'hangoutsMeet'}
                    }
                }
                insert_kwargs['conferenceDataVersion'] = 1

            if recurrence_freq and recurrence_until:
                try:
                    until_date = datetime.datetime.strptime(recurrence_until, "%Y-%m-%d").date()
                    until_datetime = datetime.datetime.combine(until_date, datetime.time.max)
                    until_rrule_str = until_datetime.strftime("%Y%m%dT%H%M%SZ")
                    rrule = f'RRULE:FREQ={recurrence_freq.upper()};UNTIL={until_rrule_str}'
                    event_body['recurrence'] = [rrule]
                except ValueError:
                    return {"status": "error", "message": "Invalid format for recurrence_until. Use YYY-MM-DD."}

            created_event = self.service.events().insert(**insert_kwargs).execute()

            response_message = f"Event '{created_event.get('summary')}' created successfully."
            if 'hangoutLink' in created_event:
                response_message += f" Google Meet link: {created_event['hangoutLink']}"

            return {"status": "success", "message": response_message, "meet_link": created_event.get('hangoutLink')}
        except HttpError as error:
            print(f"An HttpError occurred: {error.resp.status} - {error.content}")
            return {"status": "error", "message": f"An API error occurred: {error.resp.reason}"}
        except Exception as e:
            import traceback
            print(f"An unexpected error occurred in create_event:")
            traceback.print_exc()
            return {"status": "error", "message": f"An unexpected error occurred: {str(e)}"}


    def get_now(self) -> dict:
        """
        Returns the current date and time.
        """
        return {"current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M")}

    def list_events(self, max_results: int = 10) -> dict:
        """
        Lists the next 'max_results' events on the user's primary calendar.
        """
        if err := self._check_service(): return err
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
        if err := self._check_service(): return err
        try:
            self.service.events().delete(calendarId='primary', eventId=event_id).execute()
            return {"status": "success", "message": f"Event with ID '{event_id}' was removed."}
        except HttpError as error:
            return {"status": "error", "message": f"An error occurred: {error}"}

    def schedule_timetable(self, events: list) -> dict:
        """
        Schedules multiple events from a list, handling severity mapping.
        """
        if err := self._check_service(): return err
        successful_events = 0
        failed_events = 0

        severity_to_color = {
            "high": "11",   # Red
            "medium": "5",  # Yellow
            "low": "9",     # Blue
        }

        for event_data in events:
            try:
                severity = event_data.pop("severity", "low")
                color_id = severity_to_color.get(severity, "9")
                event_data["color_id"] = color_id

                result = self.create_event(**event_data)
                if result.get("status") == "success":
                    successful_events += 1
                else:
                    failed_events += 1
            except Exception as e:
                print(f"Failed to schedule an event from timetable: {e}")
                failed_events += 1

        return {
            "status": "complete",
            "message": f"Successfully scheduled {successful_events} events. {failed_events} events failed to schedule."
        }


    def get_events_by_date(self, date_str: str) -> dict:
        """
        Retrieves all events on a specific date.
        """
        if err := self._check_service(): return err
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
        """
        if err := self._check_service(): return err
        try:
            start_date = date_parse(start_date_query).date()
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

    def find_event_id(self, query: str, date_str: str) -> dict:
        """
        Finds the event ID for an event with a given summary on a specific date.
        """
        if err := self._check_service(): return err
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
                if event['summary'].lower() == query.lower():
                    return {"status": "success", "event_id": event['id']}

            return {"status": "error", "message": f"No event found with summary '{query}' on {date_str}."}
        except Exception as e:
            return {"status": "error", "message": str(e)}
