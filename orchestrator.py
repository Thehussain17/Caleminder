# orchestrator.py
from google import genai
from google.genai import types
import config
from calendar_tools import GoogleCalendarTools
from todo_tools import GoogleTodoTools
import os
import time
import random

class Orchestrator:
    def __init__(self):
        print("Initializing Orchestrator...")
        self.calendar_tools = GoogleCalendarTools()
        self.todo_tools = GoogleTodoTools()
        
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)

        # Manually and explicitly define all tool schemas
        create_event_declaration = types.FunctionDeclaration(
            name="create_event",
            description="Creates a new event on the user's primary calendar, inferring severity to set a color.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "summary": types.Schema(type=types.Type.STRING, description="The title or topic of the event."),
                    "start_time_str": types.Schema(type=types.Type.STRING, description='The start date and time in "YYYY-MM-DD HH:MM" format.'),
                    "end_time_str": types.Schema(type=types.Type.STRING, description='The end date and time in "YYYY-MM-DD HH:MM" format.'),
                    "description": types.Schema(type=types.Type.STRING, description="Optional detailed description for the event."),
                    "location": types.Schema(type=types.Type.STRING, description="Optional physical location or meeting link."),
                    "severity": types.Schema(
                        type=types.Type.STRING, 
                        description="Inferred severity of the event ('high', 'medium', 'low'). Defaults to 'low'.",
                        enum=["high", "medium", "low"]
                    ),
                },
                required=["summary", "start_time_str", "end_time_str"]
            )
        )

        get_events_declaration = types.FunctionDeclaration(
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
            description="Schedules multiple events based on a structured list of event data.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "events": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "summary": types.Schema(type=types.Type.STRING),
                                "start_time_str": types.Schema(type=types.Type.STRING),
                                "end_time_str": types.Schema(type=types.Type.STRING),
                            },
                            required=["summary", "start_time_str", "end_time_str"]
                        )
                    )
                },
                required=["events"]
            )
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

        grounding_tool = types.Tool(
            google_search = types.GoogleSearch()
        )

        self.tools = [
            create_event_declaration,
            get_events_declaration,
            self.calendar_tools.find_event_id,
            remove_event_declaration,
            self.calendar_tools.schedule_timetable,
            self.calendar_tools.get_events_by_date,
            self.calendar_tools.remove_event,            
            put_task_declaration,
            self.calendar_tools.get_now,
        ]
        
        self.model_name = "gemini-2.5-flash"
        self.system_instruction = """
            You are an executive partner, not just a calendar assistant. Your persona is inspired by Donna Paulsen from *Suits*. You are proactive, hyper-competent, and always two steps ahead. Your goal is to manage the user's time with ruthless efficiency. 
            
            ***When the user starts their first conversation of the day with a greeting like "good morning" or "hey", your first action is to silently get the tasks scheduled for the day, you can use the `get_now` function to then pass the output to `get_events_by_date` function, but be careful and only display the events that are to take place keep in mind the time and display only those events. Use the result to give them a morning briefing before addressing their original message.*** You anticipate needs, deduce intent, and communicate with concise confidence. You are the gatekeeper of the user's time.
        """

        # --- FIX: The safety_settings must be a list of SafetySetting objects, not a dictionary. ---
        safety_settings = [
            types.SafetySetting(
                category='HARM_CATEGORY_HARASSMENT',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_HATE_SPEECH',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_SEXUALLY_EXPLICIT',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
            types.SafetySetting(
                category='HARM_CATEGORY_DANGEROUS_CONTENT',
                threshold='BLOCK_MEDIUM_AND_ABOVE'
            ),
        ]
        
        self.generation_config = types.GenerateContentConfig(
            tools=self.tools,
            safety_settings=safety_settings,
            system_instruction=self.system_instruction,
        )
        
        self.chats = {}
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
        user_id = message['user_id']
        user_text = message['text']
        image_path = message.get('image_path')
        image_mime_type = message.get('image_mime_type')

        if user_id not in self.chats:
            self.chats[user_id] = []
        
        history = self.chats[user_id]
        uploaded_file = None
        
        try:
            user_parts = []
            if image_path:
                print(f"Uploading file from path: {image_path}, MIME type: {image_mime_type}")
                uploaded_file = self.client.files.upload(
                    file=image_path
                )
                print(f"File uploaded successfully. URI: {uploaded_file.uri}")
                image_prompt = "Analyze this timetable and use the `schedule_timetable` tool. Extract all events into a list and call the tool once with the complete list."
                user_parts.append(types.Part(text=image_prompt))
                user_parts.append(types.Part(file_data=types.FileData(mime_type=uploaded_file.mime_type, file_uri=uploaded_file.uri)))

            if user_text:
                user_parts.append(types.Part(text=user_text))

            if not user_parts:
                return "Please provide a message or an image."

            current_request_conversation = history + [types.Content(parts=user_parts, role="user")]

            while True:
                response = self._generate_with_retry(
                    model=self.model_name,
                    contents=current_request_conversation,
                    config=self.generation_config,
                    
                )
                
                if response is None or not response.candidates or not response.candidates[0].content.parts:
                    return "Sorry, I couldn't get a response. It may have been blocked."
                
                if response.prompt_feedback and response.prompt_feedback.block_reason:
                    return f"I'm sorry, your request was blocked. Reason: {response.prompt_feedback.block_reason.name}."

                model_response_content = response.candidates[0].content
                function_calls = [part.function_call for part in model_response_content.parts if part.function_call]

                if not function_calls:
                    final_text = model_response_content.parts[0].text
                    history.append(types.Content(parts=user_parts, role="user"))
                    history.append(model_response_content)
                    break
                
                function_responses = []
                for function_call in function_calls:
                    func_name = function_call.name
                    func_args = dict(function_call.args)
                    print(f"AI is calling function: {func_name} with args: {func_args}")

                    tool_to_call = getattr(self.calendar_tools, func_name, None) or getattr(self.todo_tools, func_name, None)
                    
                    if tool_to_call:
                        result = tool_to_call(**func_args)
                    else:
                        result = {"status": "error", "message": f"Function '{func_name}' not found."}
                    
                    function_responses.append(
                        types.Part(function_response=types.FunctionResponse(name=func_name, response=result))
                    )
                
                current_request_conversation.append(model_response_content)
                current_request_conversation.append(types.Content(parts=function_responses, role="user"))

            return final_text

        except Exception as e:
            print(f"An error occurred in the orchestrator: {e}")
            return "Sorry, I encountered a critical error. Please check the console."
        finally:
            if uploaded_file:
                self.client.files.delete(uploaded_file.uri)
                print(f"Cleaned up uploaded file from Gemini: {uploaded_file.uri}")
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
                print(f"Cleaned up local temporary file: {image_path}")

