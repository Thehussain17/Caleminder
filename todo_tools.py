import os
import pickle
import datetime
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from tzlocal import get_localzone

# Define only the scope needed for this tool
SCOPES = [
    'https://www.googleapis.com/auth/calendar',
    'https://www.googleapis.com/auth/tasks',
    'https://www.googleapis.com/auth/contacts', # Read contacts
    'https://www.googleapis.com/auth/gmail.send'       # Send emails
]

class GoogleTodoTools:
    def __init__(self):
        """Initializes the Google Tasks service."""
        self.creds = self._get_credentials()
        self.tasks_service = build('tasks', 'v1', credentials=self.creds)
        if not self.tasks_service:
            raise ConnectionError("Failed to connect to Google Tasks. Check credentials.json.")

    def _get_credentials(self):
        """Handles user authentication and token management."""
        creds = None
        if os.path.exists('token.pickle'):
            with open('token.pickle', 'rb') as token:
                creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Before refreshing, check if the necessary scopes are present
                if all(scope in creds.scopes for scope in SCOPES):
                    creds.refresh(Request())
                else:
                    creds = None # Force re-authentication if scopes are missing
        
        if not creds:
            if not os.path.exists('credentials.json'):
                raise FileNotFoundError("FATAL ERROR: credentials.json not found.")
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
        return creds

    def get_upcoming_tasks(self) -> dict:
        """Retrieves all non-completed tasks that are due today, including their due dates."""
        try:
            local_tz = get_localzone()
            now = datetime.datetime.now(local_tz)
            end_of_day = datetime.datetime.combine(now.date(), datetime.time.max, tzinfo=local_tz)

            tasklists = self.tasks_service.tasklists().list().execute()
            
            if not tasklists.get('items'):
                return {"status": "success", "tasks": [], "message": "No task lists found."}

            primary_list_id = tasklists['items'][0]['id']

            results = self.tasks_service.tasks().list(
                tasklist=primary_list_id,
                dueMax=end_of_day.isoformat(),
                showCompleted=False,
                maxResults=20
            ).execute()
            
            tasks = results.get('items', [])
            if not tasks:
                return {"status": "success", "tasks": [], "message": "You have no tasks due today."}

            # --- FIX: Return a list of objects with both title and due date ---
            task_list = []
            for task in tasks:
                task_list.append({
                    "title": task.get('title', 'No Title'),
                    "due": task.get('due', 'No due date') # Get the due date for each task
                })
            return {"status": "success", "tasks": task_list}

        except Exception as e:
            return {"status": "error", "message": f"An error occurred while fetching tasks: {str(e)}"}
        
    def put_task(self, title: str, category: str = "General", due: str = None) -> dict:
        """
        Creates a new task, automatically finding or creating a relevant task list based on a category.
        """
        try:
            # 1. Find the appropriate task list
            tasklists = self.tasks_service.tasklists().list().execute().get('items', [])
            target_list_id = None
            
            # Search for a list matching the category (case-insensitive)
            for tasklist in tasklists:
                if category.lower() == tasklist.get('title', '').lower():
                    target_list_id = tasklist['id']
                    break
            
            # 2. If no list is found, create one
            if not target_list_id:
                print(f"No task list found for category '{category}'. Creating a new one.")
                new_tasklist_body = {'title': category}
                new_tasklist = self.tasks_service.tasklists().insert(body=new_tasklist_body).execute()
                target_list_id = new_tasklist['id']
                print(f"Created new task list '{category}' with ID: {target_list_id}")

            # 3. Create the task in the target list
            task_body = {'title': title}
            if due:
                # The API expects RFC 3339 format, e.g., '2025-08-30T15:00:00.000Z'
                task_body['due'] = due 
            
            task = self.tasks_service.tasks().insert(tasklist=target_list_id, body=task_body).execute()
            
            return {"status": "success", "message": f"Task '{title}' added to list '{category}'.", "task": task}

        except Exception as e:
            return {"status": "error", "message": f"An error occurred while creating the task: {str(e)}"}
