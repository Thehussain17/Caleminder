# orchestrator.py
from google import genai
from google.genai import types
import config
from calendar_tools import GoogleCalendarTools
from todo_tools import GoogleTodoTools
from google.genai.types import Tool, GoogleSearch
from communication_tools import CommunicationTools
from search_agent import SearchAgent
from user_profile_tools import UserProfileTools
from user_database import UserDB
import os
import time
import random

class Orchestrator:
    def __init__(self):
        print("Initializing Orchestrator...")
        # Tools are initialized per-request in handle_message, but we keep declarations here.
        # Self.communication_tools etc might need update if they are stateful too.
        # For now, assuming only Google tools need per-user credentials.
        self.communication_tools = CommunicationTools()
        self.search_agent = SearchAgent()
        self.user_profile_tools = UserProfileTools()

        self.client = genai.Client(api_key=config.GEMINI_API_KEY)

        # --- TOOL DECLARATIONS ---
        search_declaration = types.FunctionDeclaration(
            name="search_for_public_event_info",
            description="Use this tool to find information about public events like sports games, holidays, or movie releases.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(type=types.Type.STRING, description="The search query (e.g., 'next Lakers game date', 'release date for new Dune movie').")
                },
                required=["query"]
            )
        )

        create_event_declaration = types.FunctionDeclaration(
            name="create_event",
            description="Creates a new event, applying a specific color based on the event's category.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "summary": types.Schema(type=types.Type.STRING, description="The title or topic of the event."),
                    "start_time_str": types.Schema(type=types.Type.STRING, description='The start date and time in "YYYY-MM-DD HH:MM" format.'),
                    "end_time_str": types.Schema(type=types.Type.STRING, description='The end date and time in "YYYY-MM-DD HH:MM" format.'),
                    "description": types.Schema(type=types.Type.STRING, description="Optional detailed description for the event."),
                    "location": types.Schema(type=types.Type.STRING, description="Optional physical location or meeting link for the event."),
                    "event_type": types.Schema(
                        type=types.Type.STRING,
                        description="The category of the event, which determines its color. Defaults to 'personal'.",
                        enum=["work", "personal", "focus_time", "health", "social", "urgent"]
                    ),
                    "recurrence_freq": types.Schema(
                        type=types.Type.STRING,
                        description="Optional frequency for a recurring event. Can be 'DAILY' or 'WEEKLY'.",
                        enum=["DAILY", "WEEKLY"]
                    ),
                    "recurrence_until": types.Schema(
                        type=types.Type.STRING,
                        description="Optional end date for recurrence in 'YYYY-MM-DD' format. Required if recurrence_freq is set."
                    ),
                    "create_meet_link": types.Schema(
                        type=types.Type.BOOLEAN,
                        description="Set to true to automatically create and attach a Google Meet link to the event. Defaults to false."
                    )
                },
                required=["summary", "start_time_str", "end_time_str"]
            )
)
        find_contact_declaration = types.FunctionDeclaration(
            name="find_contact",
            description="Finds a contact in the user's Google Contacts by name to retrieve their email address.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "name_query": types.Schema(type=types.Type.STRING, description="The name of the contact to search for.")
                },
                required=["name_query"]
            )
        )

        send_email_declaration = types.FunctionDeclaration(
            name="send_email",
            description="Sends an email to a specified recipient.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "to": types.Schema(type=types.Type.STRING, description="The recipient's email address."),
                    "subject": types.Schema(type=types.Type.STRING, description="The subject line of the email."),
                    "body": types.Schema(type=types.Type.STRING, description="The plain text content of the email body."),
                },
                required=["to", "subject", "body"]
            )
        )

        get_events_by_date_declaration = types.FunctionDeclaration(
            name="get_events",
            description="Retrieves events for a given natural language date query or date range (e.g., 'today', 'next week').",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "start_date_query": types.Schema(type=types.Type.STRING, description="The start date (e.g., 'today', 'next Monday')."),
                    "end_date_query": types.Schema(type=types.Type.STRING, description="Optional end date for a range (e.g., 'next Sunday').")
                },
                required=["start_date_query"]
            )
        )

        find_event_id_declaration = types.FunctionDeclaration(
            name="find_event_id",
            description="Searches for an event on a specific date using a query string to find its unique ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "query": types.Schema(type=types.Type.STRING, description="The search term for the event (e.g., 'Startup Meeting')."),
                    "date_str": types.Schema(type=types.Type.STRING, description='The date to search on in "YYYY-MM-DD" format.')
                },
                required=["query", "date_str"]
            )
        )

        remove_event_declaration = types.FunctionDeclaration(
            name="remove_event",
            description="Removes an event from the calendar using its unique event ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "event_id": types.Schema(type=types.Type.STRING, description="The unique ID of the event to remove.")
                },
                required=["event_id"]
            )
        )

        schedule_timetable_declaration = types.FunctionDeclaration(
            name="schedule_timetable",
            description="Schedules multiple events from a list. This is the primary tool for processing timetables from images.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "events": types.Schema(
                        type=types.Type.ARRAY,
                        description="A list of individual event objects to be scheduled.",
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "summary": types.Schema(type=types.Type.STRING),
                                "start_time_str": types.Schema(type=types.Type.STRING),
                                "end_time_str": types.Schema(type=types.Type.STRING),
                                "severity": types.Schema(type=types.Type.STRING, enum=["high", "medium", "low"]),
                                "description": types.Schema(type=types.Type.STRING),
                                "location": types.Schema(type=types.Type.STRING),
                            },
                            required=["summary", "start_time_str", "end_time_str"]
                        )
                    )
                },
                required=["events"]
            )
        )

        get_upcoming_tasks_declaration = types.FunctionDeclaration(
            name="get_upcoming_tasks",
            description="Retrieves all of the user's non-completed tasks that are due today from all of their task lists.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={})
        )

        put_task_declaration = types.FunctionDeclaration(
            name="put_task",
            description="Creates a new task, automatically finding or creating a relevant task list based on a category.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "title": types.Schema(type=types.Type.STRING, description="The title or content of the task."),
                    "category": types.Schema(type=types.Type.STRING, description="The category for the task (e.g., 'Work', 'Personal'). Defaults to 'General'."),
                    "due": types.Schema(type=types.Type.STRING, description="Optional due date in RFC 3339 format (e.g., '2025-08-30T15:00:00.000Z').")
                },
                required=["title"]
            )
        )

        get_now_declaration = types.FunctionDeclaration(
            name="get_now",
            description="Returns the current date and time in ISO format.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={})
        )

        delete_task_declaration = types.FunctionDeclaration(
            name="delete_task",
            description="Deletes a task by its unique ID from a specified task list.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "task_id": types.Schema(type=types.Type.STRING, description="The unique ID of the task to delete."),
                    "category": types.Schema(type=types.Type.STRING, description="The category of the task list (e.g., 'Work', 'Personal'). Defaults to 'General'.")
                },
                required=["task_id"]
            )
        )

        mark_task_complete_declaration = types.FunctionDeclaration(
            name="mark_task_complete",
            description="Marks a task as completed by its unique ID in a specified task list.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "task_id": types.Schema(type=types.Type.STRING, description="The unique ID of the task to mark as complete."),
                    "category": types.Schema(type=types.Type.STRING, description="The category of the task list (e.g., 'Work', 'Personal'). Defaults to 'General'.")
                },
                required=["task_id"]
            )
        )

        find_task_id_declaration = types.FunctionDeclaration(
            name="find_task_id",
            description="Finds a task by title in a specified task list and returns its unique ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "title_query": types.Schema(type=types.Type.STRING, description="The title or content of the task to search for."),
                    "category": types.Schema(type=types.Type.STRING, description="The category of the task list (e.g., 'Work', 'Personal'). Defaults to 'General'.")
                },
                required=["title_query"]
            )
        )

        # User profile tools
        get_user_profile_declaration = types.FunctionDeclaration(
            name="get_user_profile",
            description="Retrieves the current user's profile and preferences.",
            parameters=types.Schema(type=types.Type.OBJECT, properties={})
        )

        update_user_profile_declaration = types.FunctionDeclaration(
            name="update_user_profile",
            description="Updates the user's profile with new key-value pairs.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "updates": types.Schema(type=types.Type.OBJECT, description="Dictionary of profile fields to update.")
                },
                required=["updates"]
            )
        )

        # --- CONFIGURATION SETUP ---
        all_declarations = [
            create_event_declaration, get_events_by_date_declaration, find_event_id_declaration,
            remove_event_declaration, schedule_timetable_declaration, get_upcoming_tasks_declaration,
            put_task_declaration, get_now_declaration, find_contact_declaration, send_email_declaration, search_declaration
            , delete_task_declaration, mark_task_complete_declaration, find_task_id_declaration,
            get_user_profile_declaration, update_user_profile_declaration
        ]

        self.tools = [types.Tool(function_declarations=all_declarations)]

        safety_settings = [
            types.SafetySetting(category='HARM_CATEGORY_HARASSMENT', threshold='BLOCK_MEDIUM_AND_ABOVE'),
            types.SafetySetting(category='HARM_CATEGORY_HATE_SPEECH', threshold='BLOCK_MEDIUM_AND_ABOVE'),
            types.SafetySetting(category='HARM_CATEGORY_SEXUALLY_EXPLICIT', threshold='BLOCK_MEDIUM_AND_ABOVE'),
            types.SafetySetting(category='HARM_CATEGORY_DANGEROUS_CONTENT', threshold='BLOCK_MEDIUM_AND_ABOVE'),
        ]
        self.system_instruction = """
             You are proactive, hyper-competent, and always two steps ahead, a very intelligent assistant, you always put thought into your actions. Your goal is to manage the user's time with ruthless efficiency, you should also care about the users preferences and overall wellbeing

            When the user starts their first conversation of the day with a greeting based on the time, your first action is to use the tools provided to  give them a morning briefing before addressing their original message. You anticipate needs, deduce intent, and communicate with concise confidence. You are the gatekeeper of the user's time.
            also you are given access to various tools, before asking user for any information, ensure you have fully utilized the tools at your disposal to gather all necessary information. Do not ask the user for information you can obtain through the tools.
            Always think step-by-step about what information you need and how to get it using the tools. if the user asks for information about anything, use the search tool provided to you to find the details about it, but make sure you are able to help your user in any aspect they ask you. You have access to all the information on the planet.
        """
        self.generation_config = types.GenerateContentConfig(
            tools=self.tools,
            safety_settings=safety_settings,
            system_instruction = self.system_instruction,
        )

        self.model_name = "gemini-2.5-flash"

        # We don't store chats in memory anymore, we expect the handler to pass the history
        print("Orchestrator initialized.")

    def _generate_with_retry(self, **kwargs):
        """A robust method to call the Gemini API with exponential backoff."""
        max_retries = 3
        delay = 1.0
        for attempt in range(max_retries):
            try:
                return self.client.models.generate_content(**kwargs)
            except Exception as e:
                if "503" in str(e) and "UNAVAILABLE" in str(e):
                    if attempt < max_retries - 1:
                        print(f"Model overloaded (503), retrying in {delay:.2f} seconds...")
                        time.sleep(delay + random.uniform(0, 0.5))
                        delay *= 2
                    else:
                        print("Max retries reached. Failing.")
                        raise e
                else:
                    raise e
        return None

    def handle_message(self, message):
        """
        Handles an incoming message from a user.
        message dict keys:
        - user_id: str
        - text: str
        - image_path: str (optional)
        - image_mime_type: str (optional)
        - credentials: json str (optional, for Google tools)
        - history: list (optional, previous conversation history)
        """
        user_id = message['user_id']
        user_text = message['text']
        image_path = message.get('image_path')
        image_mime_type = message.get('image_mime_type')
        credentials_json = message.get('credentials')
        history = message.get('history', [])

        # Instantiate tools for this request
        current_calendar_tools = GoogleCalendarTools(credentials_json)
        current_todo_tools = GoogleTodoTools(credentials_json)
        current_communication_tools = CommunicationTools(credentials_json)

        uploaded_file = None
        new_history_items = []

        try:
            # --- CONSTRUCT THE INITIAL USER PROMPT ---
            user_parts = []
            if image_path:
                print(f"Uploading file from path: {image_path}, MIME type: {image_mime_type}")
                uploaded_file = self.client.files.upload(file=image_path)

                image_prompt = "Analyze this timetable. For each distinct event you find, call the `create_event` tool. Do not try to schedule them all at once."
                user_parts.append(types.Part(text=image_prompt))
                user_parts.append(types.Part(file_data=types.FileData(mime_type=image_mime_type, file_uri=uploaded_file.uri)))
                print('uploaded file')

            if user_text:
                print('received user text')
                user_parts.append(types.Part(text=user_text))

            if not user_parts:
                return {"text": "Please provide a message or an image.", "new_history": []}

            # Prepare conversation for the API call
            current_request_conversation = history + [types.Content(parts=user_parts, role="user")]

            # --- THE CONVERSATIONAL LOOP ---
            final_text = ""
            while True:
                print("Sending request to Gemini...")
                response = self._generate_with_retry(
                            model=self.model_name,
                            contents=current_request_conversation,
                            config=self.generation_config,
                    )
                print("Received response from Gemini.")

                if response is None:
                        return {"text": "Sorry, the model is currently unavailable. Please try again later.", "new_history": []}

                if response.prompt_feedback and response.prompt_feedback.block_reason:
                        return {"text": f"I'm sorry, your request was blocked. Reason: {response.prompt_feedback.block_reason.name}.", "new_history": []}

                if not response.candidates or not response.candidates[0].content:
                        return {"text": "I'm sorry, I couldn't generate a response. It may have been blocked.", "new_history": []}

                model_response_content = response.candidates[0].content
                function_calls = [part.function_call for part in model_response_content.parts if part.function_call]
                print('recieved necessary content')

                if not function_calls:
                        # No function call, this is the final text response.
                        final_text = model_response_content.parts[0].text

                        # Add to history (only the new turns)
                        new_history_items.append(types.Content(parts=user_parts, role="user"))
                        new_history_items.append(model_response_content)
                        break

                # --- EXECUTE TOOLS ---
                function_responses = []
                for function_call in function_calls:
                    func_name = function_call.name
                    func_args = dict(function_call.args)
                    print(f"AI is calling function: {func_name} with args: {func_args}")

                    if func_name == "search_for_public_event_info":
                        result = self.search_agent.execute_search(**func_args)
                    else:
                        tool_to_call = None
                        # Use the user-instantiated tools
                        if hasattr(current_calendar_tools, func_name):
                            tool_to_call = getattr(current_calendar_tools, func_name)
                        elif hasattr(current_todo_tools, func_name):
                            tool_to_call = getattr(current_todo_tools, func_name)
                        elif hasattr(current_communication_tools, func_name):
                            tool_to_call = getattr(current_communication_tools, func_name)
                        elif hasattr(self.user_profile_tools, func_name):
                            if func_name in ["get_user_profile", "update_user_profile"]:
                                func_args['user_id'] = user_id
                            tool_to_call = getattr(self.user_profile_tools, func_name)

                        if tool_to_call:
                            result = tool_to_call(**func_args)
                        else:
                            result = {"status": "error", "message": f"Function '{func_name}' not found."}

                    function_responses.append(
                        types.Part(function_response=types.FunctionResponse(name=func_name, response=result))
                    )

                # Append model response (with function calls) to conversation
                current_request_conversation.append(model_response_content)
                # Append function responses to conversation
                current_request_conversation.append(types.Content(parts=function_responses, role="user"))

                # We need to track these intermediate turns for history if we want to save full context
                # Ideally, we save the full chain.
                # However, the simple logic above only saves the initial user prompt and the final text.
                # To be robust, we should probably return the *entire* updated history or the delta.
                # For simplicity in this refactor, let's just return the final text and assume the orchestrator isn't responsible for saving history to DB, the handler is.
                # BUT, the loop adds to `current_request_conversation`.
                # We should capture all turns.

                # Let's actually just return the full updated conversation history list so the handler can save it.
                # The handler passed `history`, we appended to `current_request_conversation`.
                # So `current_request_conversation` IS the new history.

            return {"text": final_text, "new_history": current_request_conversation}

        except Exception as e:
            import traceback
            print(f"An error occurred in the orchestrator:")
            traceback.print_exc()
            return {"text": "Sorry, a critical error occurred.", "new_history": []}
        finally:
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
                print(f"Cleaned up local temporary file: {image_path}")
