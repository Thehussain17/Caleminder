# orchestrator.py
from google import genai
from google.genai import types
from PIL import Image
import config
from calendar_tools import GoogleCalendarTools

class Orchestrator:
    def __init__(self):
        print("Initializing Orchestrator...")
        self.calendar_tools = GoogleCalendarTools()
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        
        # Manually define the tool schema for stability and clarity.
        create_event_declaration = types.FunctionDeclaration(
            name="create_event",
            description="Creates a new event on the user's primary calendar.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "summary": types.Schema(type=types.Type.STRING, description="The title or topic of the event."),
                    "start_time_str": types.Schema(type=types.Type.STRING, description='The start date and time in "YYYY-MM-DD HH:MM" format.'),
                    "end_time_str": types.Schema(type=types.Type.STRING, description='The end date and time in "YYYY-MM-DD HH:MM" format.'),
                    "description": types.Schema(type=types.Type.STRING, description="A detailed description or notes for the event."),
                    "location": types.Schema(type=types.Type.STRING, description="The physical location or meeting link for the event."),
                    "severity": types.Schema(
                        type=types.Type.STRING, 
                        description="The severity of the event, inferred from the summary. Can be 'high', 'medium', or 'low'. Defaults to 'low' if unspecified.",
                        enum=["high", "medium", "low"]
                    ),
                },
                required=["summary", "start_time_str", "end_time_str"]
            )
        )

        # As you add more tools to calendar_tools.py, add their declarations here.
        get_now_declaration = types.FunctionDeclaration(
            name="get_now",
            description="Returns the current date and time in YYYY-MM-DD HH:MM format. you can use this function to get tomorrow and day after by just using the basic logic of the dates, you dont have to ask the user for specific dates",
            parameters=types.Schema(type=types.Type.OBJECT, properties={}, required=[])
        )

        list_events_declaration = types.FunctionDeclaration(
            name="list_events",
            description="Lists the next 'max_results' events on the user's primary calendar.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "max_results": types.Schema(type=types.Type.INTEGER, description="The maximum number of events to return.")
                },
                required=[]
            )
        )

        remove_event_declaration = types.FunctionDeclaration(
            name="remove_event",
            description="Removes an event from the user's primary calendar by event ID.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "event_id": types.Schema(type=types.Type.STRING, description="The unique identifier of the event to remove.")
                },
                required=["event_id"]
            )
        )

        schedule_timetable_declaration = types.FunctionDeclaration(
            name="schedule_timetable",
            description="Schedules multiple events based on a provided timetable.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "events": types.Schema(
                        type=types.Type.ARRAY,
                        items=types.Schema(
                            type=types.Type.OBJECT,
                            properties={
                                "summary": types.Schema(type=types.Type.STRING, description="The title or topic of the event."),
                                "start_time_str": types.Schema(type=types.Type.STRING, description='The start date and time in "YYYY-MM-DD HH:MM" format.'),
                                "end_time_str": types.Schema(type=types.Type.STRING, description='The end date and time in "YYYY-MM-DD HH:MM" format.'),
                                "description": types.Schema(type=types.Type.STRING, description="A detailed description or notes for the event."),
                                "location": types.Schema(type=types.Type.STRING, description="The physical location or meeting link for the event."),
                                "severity": types.Schema(
                                    type=types.Type.STRING, 
                                    description="The severity of the event, inferred from the summary. Can be 'high', 'medium', or 'low'. Defaults to 'low' if unspecified.",
                                    enum=["high", "medium", "low"]
                                ),
                            },
                            required=["summary", "start_time_str", "end_time_str"]
                        ),
                        description="A list of events to schedule."
                    )
                },
                required=["events"]
            )
        )

        get_events_by_date_declaration = types.FunctionDeclaration(
            name="get_event_by_date",
            description="Retrieves events occurring on a specific date.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "date_str": types.Schema(type=types.Type.STRING, description='The date in "YYYY-MM-DD" format to retrieve events for.')
                },
                required=["date_str"]
            )
        )
        get_events_declaration = types.FunctionDeclaration(
            name="get_events",
            description="Retrieves all events for a given date or date range. For 'next week', the AI should calculate the start and end dates and provide both.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "start_date_query": types.Schema(type=types.Type.STRING, description="The start date of the range (e.g., 'today', 'next Monday')."),
                    "end_date_query": types.Schema(type=types.Type.STRING, description="The optional end date of the range (e.g., 'next Sunday'). If omitted, events for a single day are fetched.")
                },
                required=["start_date_query"]
            )
        )
        
        # This is a cleaner pattern for organizing the setup.
        self.tools = types.Tool(function_declarations=[get_events_declaration,get_events_by_date_declaration,create_event_declaration, get_now_declaration, list_events_declaration, remove_event_declaration, schedule_timetable_declaration])
        # The SDK parameter is 'generation_config', not 'config'. This is a necessary correction.
        
        
        self.model_name = "gemini-2.5-flash"
        self.sessions = {} # Stores conversation history per user
        self.system_prompt = "You are a helpful assistant that manages a user's calendar. You are also suppose to help the user manage its time effectively. If the user ever asks for your opinions, you the best of your abilities to service the user. Use the provided tools to handle scheduling tasks efficiently."
        self.config = types.GenerateContentConfig(tools=[self.tools])
        print("Orchestrator initialized.")

    

    def handle_message(self, message):
        """
        Orchestrates the multi-step conversation with the Gemini model to handle
        user requests and call the appropriate tools, including parallel calls.
        """
        user_id = message['user_id']
        user_text = message['text']
        image_file = message.get('image')

        if user_id not in self.sessions:
            self.sessions[user_id] = []
        history = self.sessions[user_id]
        
        try:
            # Step 1: Prepare the user's message for the model
            contents = []
            if image_file:
                # --- FIX: Correctly handle image data and MIME type ---
                # Read the raw bytes from the file stream provided by Flask
                image_bytes = image_file.read()
                # Get the mimetype from the file object
                mime_type = image_file.mimetype
                
                image_prompt = "Analyze this timetable and use the create_event tool for each event found. Assume events are 1 hour long if no end time is specified."
                contents.append(types.Part(text=image_prompt))
                
                # Create a Blob object with the data and mimetype, then create a Part from it
                image_part = types.Part.from_bytes(data=image_bytes, mime_type=mime_type)
                contents.append(image_part)
            if user_text:
                contents.append(types.Part(text=user_text))

            request_contents = history + contents
            
            # Step 2: Send the request to the model
            response = self.client.models.generate_content(
                model=self.model_name,
                
                contents=request_contents,
                config=self.config
            )
            
            # --- NEW: Logic to handle multiple, parallel function calls ---
            while True:
                response = self.client.models.generate_content(
                    model=self.model_name,
                    contents=request_contents,
                    config=self.config
                )
                
                if not response.candidates or not response.candidates[0].content.parts:
                    return "I'm sorry, I couldn't generate a response. Please try again."

                function_calls = [part.function_call for part in response.candidates[0].content.parts if part.function_call]

                if not function_calls:
                    # If there are no more function calls, the model has its final answer.
                    final_text = response.candidates[0].content.parts[0].text
                    break # Exit the loop

                # --- Execute all function calls returned by the model ---
                function_responses = []
                for function_call in function_calls:
                    function_name = function_call.name
                    function_args = function_call.args
                    print(f"AI is calling function: {function_name} with args: {function_args}")

                    if function_name == "create_event":
                        severity_to_color = {"high": "11", "medium": "5", "low": "9"}
                        severity = function_args.pop("severity", "low") 
                        function_args["color_id"] = severity_to_color.get(severity, "9")
                        result = self.calendar_tools.create_event(**function_args)
                    elif function_name == "get_now":
                        result = self.calendar_tools.get_now()
                    elif function_name == "get_events_by_date":
                        result = self.calendar_tools.get_events_by_date(**function_args)
                        
                    

                    elif function_name == "list_events":
                        result = self.calendar_tools.list_events(**function_args)

                    elif function_name == "remove_event":
                        result = self.calendar_tools.remove_event(**function_args)
                    elif function_name == "schedule_timetable":
                        result = self.calendar_tools.schedule_timetable(**function_args)
                    elif function_name == "get_events":
                        result = self.calendar_tools.get_events(**function_args)

                                        
                    else:
                        result = {"status": "error", "message": f"Function '{function_name}' not found."}

                    function_responses.append(
                        types.Part(function_response=types.FunctionResponse(name=function_name, response=result))
                    )
                
                # --- Prepare for the next loop iteration ---
                # Add the model's function call requests and the results to the conversation history
                request_contents += response.candidates[0].content.parts + function_responses

            # --- Update the final conversation history ---
            history.extend(contents) # The original user prompt
            history.append(response.candidates[0].content) # The final model response
            
            return final_text

        except Exception as e:
            print(f"An error occurred in the orchestrator: {e}")
            return "Sorry, I encountered an error while processing your request."
            # function_calls = [part.function_call for part in response.candidates[0].content.parts if part.function_call]

            # if function_calls:
            #     function_responses = []
                
            #     # Loop through all function calls the model wants to make
            #     for function_call in function_calls:
            #         function_name = function_call.name
            #         function_args = function_call.args
            #         print(f"AI is calling function: {function_name} with args: {function_args}")

            #         # Execute the correct function based on the name
                    

            #         # Append the result of this specific call to our list of responses
            #         function_responses.append(
            #             types.Part(function_response=types.FunctionResponse(name=function_name, response=result))
            #         )

            #     # Send the original user prompt, the model's first response (with the calls),
            #     # and all the function results back to the model for a final summary.
            #     second_request_contents = request_contents + response.candidates[0].content.parts + function_responses

            #     final_response = self.client.models.generate_content(
            #         model=self.model_name,
            #         contents=second_request_contents,
            #         config=self.config
            #     )
            #     final_text = final_response.candidates[0].content.parts[0].text
                
            #     history.extend(contents)
            #     history.extend(final_response.candidates[0].content.parts)

            # else:
            #     # If no function calls, the logic is simple
            #     final_text = response.candidates[0].content.parts[0].text
            #     history.extend(contents)
            #     history.extend(response.candidates[0].content.parts)
            
            # return final_text

        # except Exception as e:
        #     print(f"An error occurred in the orchestrator: {e}")
        #     return "Sorry, I encountered an error while processing your request."
