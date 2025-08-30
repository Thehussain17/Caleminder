# orchestrator.py
import google.generativeai as genai
import config
from calendar_tools import GoogleCalendarTools
from todo_tools import GoogleTodoTools
import os
import time   # For handling retries
import random # For adding jitter to retries

# --- FIX: Use the correct import and configure the API key globally ---
genai.configure(api_key=config.GEMINI_API_KEY)

class Orchestrator:
    def __init__(self):
        print("Initializing Orchestrator...")
        self.calendar_tools = GoogleCalendarTools()
        self.todo_tools = GoogleTodoTools()
        
        self.tools = [
            self.calendar_tools.create_event,
            self.calendar_tools.get_events,
            self.calendar_tools.find_event_id,
            self.calendar_tools.remove_event,
            self.calendar_tools.schedule_timetable,
            self.todo_tools.get_upcoming_tasks,
            self.todo_tools.put_task,
        ]
        
        self.model_name = "gemini-2.5-flash"
        self.system_instruction = """
            You are an executive partner, not just a calendar assistant. Your persona is inspired by Donna Paulsen from *Suits*. You are proactive, hyper-competent, and always two steps ahead. Your goal is to manage the user's time with ruthless efficiency. When the user starts their first conversation of the day, your first action is to silently call the `get_upcoming_tasks` tool and use the result to give them a morning briefing. You anticipate needs, deduce intent, and communicate with concise confidence. You are the gatekeeper of the user's time.
        """

        self.safety_settings = {
            'HARM_CATEGORY_HARASSMENT': 'BLOCK_MEDIUM_AND_ABOVE',
            'HARM_CATEGORY_HATE_SPEECH': 'BLOCK_MEDIUM_AND_ABOVE',
            'HARM_CATEGORY_SEXUALLY_EXPLICIT': 'BLOCK_MEDIUM_AND_ABOVE',
            'HARM_CATEGORY_DANGEROUS_CONTENT': 'BLOCK_MEDIUM_AND_ABOVE',
        }

        # --- FIX: The tools MUST be defined when the model is created. ---
        self.model = genai.GenerativeModel(
            model_name=self.model_name,
            tools=self.tools,
            system_instruction=self.system_instruction,
            safety_settings=self.safety_settings
        )
        
        self.chats = {}

        print("Orchestrator initialized.")

    def _generate_with_retry(self, chat_session, content):
        """
        A robust method to call the Gemini API with exponential backoff.
        """
        max_retries = 3
        delay = 1.0
        for attempt in range(max_retries):
            try:
                return chat_session.send_message(content)
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
            # --- FIX: start_chat inherits tools from the parent model. ---
            self.chats[user_id] = self.model.start_chat(
                enable_automatic_function_calling=True
            )
        chat_session = self.chats[user_id]
        
        uploaded_file = None
        
        try:
            contents = []
            if image_path:
                print(f"Uploading file from path: {image_path}, MIME type: {image_mime_type}")
                uploaded_file = genai.upload_file(
                    path=image_path,
                    mime_type=image_mime_type
                )
                print(f"File uploaded successfully. URI: {uploaded_file.uri}")
                image_prompt = "Analyze this timetable and use the `schedule_timetable` tool. Extract all events into a list and call the tool once with the complete list."
                contents.append(image_prompt)
                contents.append(uploaded_file)
            
            if user_text:
                contents.append(user_text)

            if not contents:
                return "Please provide a message or an image."
            
            response = self._generate_with_retry(
                chat_session=chat_session,
                content=contents
            )
            
            if response is None:
                 return "Sorry, I couldn't get a response from the model after multiple retries."

            if response.prompt_feedback.block_reason:
                print(f"Request was blocked. Reason: {response.prompt_feedback.block_reason.name}")
                print(f"Safety Ratings: {response.prompt_feedback.safety_ratings}")
                return f"I'm sorry, your request was blocked. Reason: {response.prompt_feedback.block_reason.name}."

            final_text = response.text if response and response.text else "I've handled that for you."
            return final_text

        except Exception as e:
            print(f"An error occurred in the orchestrator: {e}")
            return "Sorry, I encountered a critical error while processing your request. Please check the console."
        finally:
            # Cleanup logic
            if uploaded_file:
                genai.delete_file(uploaded_file.name)
                print(f"Cleaned up uploaded file from Gemini: {uploaded_file.name}")
            if image_path and os.path.exists(image_path):
                os.remove(image_path)
                print(f"Cleaned up local temporary file: {image_path}")

