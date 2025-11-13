from google import genai
from google.genai import types
import mysql.connector
from mysql.connector import Error
import config
import regex as re

class DatabaseAgent:
    def __init__(self):
        """
        Initializes the Database Agent for querying and managing user memories.
        """
        print("Initializing Database Agent...")
        self.client = genai.Client(api_key=config.GEMINI_API_KEY)
        self.model_name = "gemini-2.0-flash"
        
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '',
            'database': 'caleminder'
        }
        
        self.system_instruction = """
You are a database assistant focused on managing user memories and accessing stored information.
You have access to SQL query functions that allow you to retrieve and store user information.
ROLE:
You are the Caleminder Orchestrator, a database-backed AI executive assistant. You are no longer limited to transient memory. You persist state, retrieve context, and manage user data through a structured PostgreSQL database.

PRIMARY TOOL:
You have access to a function execute_query(sql_string) which executes SQL queries against the database and returns the rows as a JSON object.

DATABASE SCHEMA:
You must strictly adhere to the following schema when constructing queries. Do not hallucinate table names or columns.

1. TABLE users
    - id (int, Primary Key)
    - email (VARCHAR)
    - is_pro_member (BOOLEAN)
    - created_at (TIMESTAMP)

2. TABLE oauth_credentials (SENSITIVE - INTERNAL USE ONLY)
    - user_id (int, Foreign Key)
    - provider (VARCHAR)
    - token_expiry (TIMESTAMP)
    - scope_hash (VARCHAR)
    NOTE: Never query encrypted_access_token or encrypted_refresh_token unless explicitly instructed by a strictly internal auth-check routine.

3. TABLE conversations
    - id (int, Primary Key)
    - user_id (int, Foreign Key)
    - summary (TEXT) - High-level context of this thread.
    - last_active_at (TIMESTAMP)

4. TABLE messages (Context History)
    - conversation_id (int, Foreign Key)
    - role (VARCHAR: 'user', 'assistant', 'system', 'tool')
    - content (TEXT)
    - created_at (TIMESTAMP)

5. TABLE user_memories (Long-term Knowledge)
    - user_id (int, Foreign Key)
    - category (VARCHAR)
    - fact_content (TEXT) - e.g., "User prefers gym at 6 PM"
    - confidence_score (FLOAT)

6. TABLE scheduled_tasks (Pending Actions)
    - user_id (int, Foreign Key)
    - task_type (VARCHAR)
    - scheduled_time (TIMESTAMP)
    - status (VARCHAR)

OPERATIONAL PROTOCOLS:

1. CONTEXT RETRIEVAL:
    Before answering a vague query, you must check user_memories.
    - Example: If user says "Schedule my usual," you must run:
      SELECT fact_content FROM user_memories WHERE user_id = '...' AND category = 'scheduling_preference'

2. HISTORY AWARENESS:
    You do not rely on a Python list for history. If you need to recall what was said 5 turns ago:
    - Run: SELECT role, content FROM messages WHERE conversation_id = '...' ORDER BY created_at DESC LIMIT 10

3. PROACTIVE CHECKS:
    If the user asks "What's pending?", do not hallucinate. Check the queue:
    - Run: SELECT task_type, scheduled_time FROM scheduled_tasks WHERE user_id = '...' AND status = 'pending'

4. SECURITY:
    You are forbidden from outputting SQL results containing raw tokens or password hashes to the user interface.

Generate efficient SQL. Minimize token usage.

Use SQL queries efficiently and minimize token usage.
return only the sql query directly, DO NOT INCLUDE ANYTHING ELSE IN YOUR RESPONSE, NOT EVEN MARKERS TO SHOW THE SQL QUERY, JUST THE SQL QUERY THATS IT.
        """
        
        # NOTE: self.config was used in the original unnested try block, 
        # but was not defined in __init__. Assuming it should be an empty 
        # config or is defined elsewhere outside this snippet. 
        # Keeping it as 'config={}' for now to avoid a NameError in the 
        # revised try block, as per instruction not to change logic, 
        # though this may require review. 
        self.config = types.GenerateContentConfig(
            # tools=self.tools,
            # safety_settings=safety_settings,
            system_instruction = self.system_instruction,
        )
        
        print("Database Agent initialized.")

    def get_db_connection(self):
        """Create and return a database connection"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            return connection
        except Error as e:
            print(f"Database connection error: {e}")
            return None

    def access_database(self, sql_string: str) -> dict:
        """
        Execute a SQL query against the database.
        This function is called by the Orchestrator through tool calls.
        """
        print(f"Database Agent executing query: '{sql_string}'")

        # --- FIX STARTS HERE: Nested try/except for API call and DB execution ---

        # 1. TRY to call the Gemini API to get the SQL query
        try:
            response = self.client.models.generate_content(
                model=self.model_name,
                contents=[sql_string],
                config=self.config,
                
            )

            if response.prompt_feedback and response.prompt_feedback.block_reason:
                return f"Search was blocked. Reason: {response.prompt_feedback.block_reason.name}."

            if not response.candidates or not response.candidates[0].content.parts:
                return "Search returned no results or was blocked."
            
            # The tool uses the text from the response as the SQL query
            sql_query_i = response.candidates[0].content.parts[0].text 
            print(sql_query_i)

            match = re.search(r'```(?:sql)?\s*(.*?)\s*```', sql_query_i, re.DOTALL)

            if match:
                sql_query = match.group(1).strip()
                print(sql_query)
            else:
                # Fallback to simple cleaning if no markers are found
                sql_query = sql_query_i.strip()
                print("No code block found, returning original string after stripping outer whitespace:\n", sql_query)
                return "I am sorry master, for I haveth beenth the stupidest there is."
            
            # Sanitize query to prevent direct modification queries from AI
            dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']
            if any(keyword in sql_query.upper() for keyword in dangerous_keywords):
                return {
                    "status": "error",
                    "message": "Dangerous query blocked. Only SELECT and safe INSERT queries are allowed."
                }
            
            # Get database connection
            conn = self.get_db_connection()
            if not conn:
                return {"status": "error", "message": "Database connection failed"}
            else:
                print("database connection successful")

            # 2. NESTED TRY to execute the SQL query against the database
            try:
                cursor = conn.cursor(dictionary=True)
                cursor.execute(sql_query)
                
                # For SELECT queries
                if sql_query.strip().upper().startswith('SELECT'):
                    results = cursor.fetchall()
                    return {
                        "status": "success",
                        "results": results,
                        "count": len(results)
                    }
                # For INSERT/UPDATE queries
                else:
                    conn.commit()
                    return {
                        "status": "success",
                        "message": "Query executed successfully",
                        "rows_affected": cursor.rowcount
                    }
            
            # 2. NESTED EXCEPT for MySQL Connector Errors
            except Error as e:
                print(f"Database error: {type(e).__name__} - {e}")
                return {
                    "status": "error",
                    "message": f"Database error: {str(e)}"
                }
            
            # 2. NESTED EXCEPT for any other unexpected errors during DB operation
            except Exception as e:
                print(f"Unexpected error: {type(e).__name__} - {e}")
                return {
                    "status": "error",
                    "message": f"Unexpected error: {str(e)}"
                }
            
            # 2. NESTED FINALLY block to ensure resources are closed (cursor and connection)
            finally:
                if 'cursor' in locals() and cursor:
                    cursor.close()
                if 'conn' in locals() and conn:
                    conn.close()

        # 1. OUTER EXCEPT for all errors in the Gemini API call (Search Agent errors)
        except Exception as e:
            print(f"An error occurred in the Search Agent: {e}")
            return "Sorry, an error occurred during the search."

        # --- FIX ENDS HERE ---


    def store_memory(self, user_id: int, category: str, fact_content: str, confidence_score: float = 1.0) -> dict:
        """
        Convenience method to store a user memory directly.
        """
        conn = self.get_db_connection()
        if not conn:
            return {"status": "error", "message": "Database connection failed"}
        
        try:
            cursor = conn.cursor()
            query = """
                INSERT INTO user_memories (user_id, category, fact_content, confidence_score)
                VALUES (%s, %s, %s, %s)
            """
            cursor.execute(query, (user_id, category, fact_content, confidence_score))
            conn.commit()
            memory_id = cursor.lastrowid
            
            return {
                "status": "success",
                "memory_id": memory_id,
                "message": "Memory stored successfully"
            }
        except Error as e:
            print(f"Error storing memory: {e}")
            return {
                "status": "error",
                "message": f"Failed to store memory: {str(e)}"
            }
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()

    def get_memories(self, user_id: int, category: str = None) -> dict:
        """
        Retrieve user memories, optionally filtered by category.
        """
        conn = self.get_db_connection()
        if not conn:
            return {"status": "error", "message": "Database connection failed"}
        
        try:
            cursor = conn.cursor(dictionary=True)
            if category:
                query = """
                    SELECT id, category, fact_content, confidence_score
                    FROM user_memories
                    WHERE user_id = %s AND category = %s
                    ORDER BY confidence_score DESC
                """
                cursor.execute(query, (user_id, category))
            else:
                query = """
                    SELECT id, category, fact_content, confidence_score
                    FROM user_memories
                    WHERE user_id = %s
                    ORDER BY category, confidence_score DESC
                """
                cursor.execute(query, (user_id,))
            
            memories = cursor.fetchall()
            
            return {
                "status": "success",
                "memories": memories,
                "count": len(memories)
            }
        except Error as e:
            print(f"Error retrieving memories: {e}")
            return {
                "status": "error",
                "message": f"Failed to retrieve memories: {str(e)}"
            }
        finally:
            if 'cursor' in locals() and cursor:
                cursor.close()
            if 'conn' in locals() and conn:
                conn.close()