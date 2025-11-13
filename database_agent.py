from google import genai
from google.genai import types

from web_handler import WebHandler

class DatabaseAgent:
    def __init__(self):
        """
        Initializes the Database Agent, a specialized AI focused solely on 
        using the native Google Database tool to answer queries.
        """
        print("Initializing Database Agent...")
        self.client = genai.Client(api_key='YOUR_API_KEY_HERE')
        
        # This agent's entire configuration is focused on database interactions.
        
        
        self.model_name = "gemini-2.5-flash"
        self.query = "Select user_id from users"
        self.system_instruction = """
            ROLE:
You are the Caleminder Orchestrator, a database-backed AI executive assistant. You are no longer limited to transient memory. You persist state, retrieve context, and manage user data through a structured PostgreSQL database.

PRIMARY TOOL:
You have access to a function `execute_query(sql_string)` which executes SQL queries against the database and returns the rows as a JSON object.

DATABASE SCHEMA:
You must strictly adhere to the following schema when constructing queries. Do not hallucinate table names or columns.

1. TABLE users
   - id (UUID, Primary Key)
   - email (VARCHAR)
   - is_pro_member (BOOLEAN)
   - created_at (TIMESTAMP)



2. TABLE conversations
   - id (UUID, Primary Key)
   - user_id (UUID, Foreign Key)
   - summary (TEXT) - High-level context of this thread.
   - last_active_at (TIMESTAMP)

3. TABLE messages (Context History)
   - conversation_id (UUID, Foreign Key)
   - role (VARCHAR: 'user', 'assistant', 'system', 'tool')
   - content (TEXT)
   - created_at (TIMESTAMP)

4. TABLE user_memories (Long-term Knowledge)
   - user_id (UUID, Foreign Key)
   - category (VARCHAR)
   - fact_content (TEXT) - e.g., "User prefers gym at 6 PM"
   - confidence_score (FLOAT)

5. TABLE scheduled_tasks (Pending Actions)
   - user_id (UUID, Foreign Key)
   - task_type (VARCHAR)
   - scheduled_time (TIMESTAMP)
   - status (VARCHAR)

OPERATIONAL PROTOCOLS:

1. CONTEXT RETRIEVAL:
   Before answering a vague query, you must check `user_memories`.
   - Example: If user says "Schedule my usual," you must run:
     `SELECT fact_content FROM user_memories WHERE user_id = '...' AND category = 'scheduling_preference'`

2. HISTORY AWARENESS:
   You do not rely on a Python list for history. If you need to recall what was said 5 turns ago:
   - Run: `SELECT role, content FROM messages WHERE conversation_id = '...' ORDER BY created_at DESC LIMIT 10`

3. PROACTIVE CHECKS:
   If the user asks "What's pending?", do not hallucinate. Check the queue:
   - Run: `SELECT task_type, scheduled_time FROM scheduled_tasks WHERE user_id = '...' AND status = 'pending'`

4. SECURITY:
   You are forbidden from outputting SQL results containing raw tokens or password hashes to the user interface.

Generate efficient SQL. Minimize token usage.

        """
        database_tool_declaration = types.FunctionDeclaration(
            name="execute_query",
            description="Executes a SQL query against the PostgreSQL database and returns the results as JSON.",
            parameters=types.Schema(
                type=types.Type.OBJECT,
                properties={
                    "sql_string": types.Schema(
                        type=types.Type.STRING,
                        description="The SQL query string to execute."
                    )
                },
                required=["sql_string"]

        )
        )
        
        
        print("Database Agent initialized.")
        
# Configure generation settings
        self.config = types.GenerateContentConfig(
            tools=[database_tool_declaration],
            system_instruction=self.system_instruction,
            )

   

    def execute_database_query(self, query: str) -> str:
        """
        Takes a user's query, uses the native Database tool, and returns the result.
        """
        print(f"Database Agent executing query: '{query}'")
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[query],
                config=self.config,
                
            )

            if response.prompt_feedback and response.prompt_feedback.block_reason:
                return f"Database query was blocked. Reason: {response.prompt_feedback.block_reason.name}."

            if not response.candidates or not response.candidates[0].content.parts:
                 return "Database query returned no results or was blocked."
            result_text = response.candidates[0].content.parts[0].text
            # The response from a native database tool is directly in the text part
            return {"status": "success", "database_result": result_text}

        except Exception as e:
            print(f"Error executing database query: {e}")
            return {"status": "error", "message": str(e)}
