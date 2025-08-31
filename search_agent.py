# search_agent.py
from google import genai
from google.genai import types

import config

class SearchAgent:
    def __init__(self):
        """
        Initializes the Search Agent, a specialized AI focused solely on 
        using the native Google Search tool to answer queries.
        """
        print("Initializing Search Agent...")
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        
        # This agent's entire configuration is focused on search.
        
        
        self.model_name = "gemini-2.5-flash"
        
        self.system_instruction = """
            You are a specialized search agent. Your only function is to use the provided Google Search tool to answer the user's query.
            You must provide a direct, factual summary of the search results. Do not add any conversational fluff or commentary.
            Your response should contain only the information found, formatted clearly. also get the results most relevant to the user based on Indian Standard Time.

        """

        
        
        print("Search Agent initialized.")
        grounding_tool = types.Tool(
        google_search=types.GoogleSearch()
      )

# Configure generation settings
        self.config = types.GenerateContentConfig(
            tools=[grounding_tool],
            system_instruction=self.system_instruction,
            )

    def execute_search(self, query: str) -> str:
        """
        Takes a user's query, uses the native Google Search tool, and returns the result.
        """
        print(f"Search Agent executing query: '{query}'")
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[query],
                config=self.config,
                
            )

            if response.prompt_feedback and response.prompt_feedback.block_reason:
                return f"Search was blocked. Reason: {response.prompt_feedback.block_reason.name}."

            if not response.candidates or not response.candidates[0].content.parts:
                 return "Search returned no results or was blocked."
            result_text = response.candidates[0].content.parts[0].text
            # The response from a native search tool is directly in the text part
            return {"status": "success", "search_result": result_text}

        except Exception as e:
            print(f"An error occurred in the Search Agent: {e}")
            return "Sorry, an error occurred during the search."
