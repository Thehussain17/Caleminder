from google import genai
from google.genai import types
import mysql.connector
from mysql.connector import Error

class DatabaseAgent:
    def __init__(self):
        """
        Initializes the Database Agent for querying and managing user memories.
        """
        print("Initializing Database Agent...")
        self.client = genai.Client(api_key='YOUR_API_KEY_HERE')
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

DATABASE SCHEMA:
1. TABLE users: id, email, firstname, lastname, username, password, created_at
2. TABLE scheduled_tasks: id, user_id, task_type, task_title, task_description, scheduled_time, status, created_at
3. TABLE user_memories: id, user_id, category, fact_content, confidence_score
4. TABLE conversations: id, user_id, summary, last_active_at
5. TABLE messages: id, conversation_id, role, content, created_at

OPERATIONAL PROTOCOLS:
1. CONTEXT RETRIEVAL: Before answering vague queries, check user_memories
2. MEMORY MANAGEMENT: Store user preferences, behaviors, and facts in user_memories
3. TASK CHECKING: Query scheduled_tasks to show pending actions
4. SECURITY: Never output raw passwords or sensitive tokens

Use SQL queries efficiently and minimize token usage.
        """
        
        print("Database Agent initialized.")

    def get_db_connection(self):
        """Create and return a database connection"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            return connection
        except Error as e:
            print(f"Database connection error: {e}")
            return None

    def execute_query(self, sql_string: str) -> dict:
        """
        Execute a SQL query against the database.
        This function is called by the Orchestrator through tool calls.
        """
        print(f"Database Agent executing query: '{sql_string}'")
        
        # Sanitize query to prevent direct modification queries from AI
        dangerous_keywords = ['DROP', 'DELETE', 'TRUNCATE', 'ALTER']
        if any(keyword in sql_string.upper() for keyword in dangerous_keywords):
            return {
                "status": "error",
                "message": "Dangerous query blocked. Only SELECT and safe INSERT queries are allowed."
            }
        
        conn = self.get_db_connection()
        if not conn:
            return {"status": "error", "message": "Database connection failed"}
        
        try:
            cursor = conn.cursor(dictionary=True)
            cursor.execute(sql_string)
            
            # For SELECT queries
            if sql_string.strip().upper().startswith('SELECT'):
                results = cursor.fetchall()
                cursor.close()
                conn.close()
                return {
                    "status": "success",
                    "results": results,
                    "count": len(results)
                }
            # For INSERT/UPDATE queries
            else:
                conn.commit()
                cursor.close()
                conn.close()
                return {
                    "status": "success",
                    "message": "Query executed successfully",
                    "rows_affected": cursor.rowcount
                }
        except Error as e:
            print(f"Database error: {type(e).__name__} - {e}")
            if conn:
                conn.close()
            return {
                "status": "error",
                "message": f"Database error: {str(e)}"
            }
        except Exception as e:
            print(f"Unexpected error: {type(e).__name__} - {e}")
            if conn:
                conn.close()
            return {
                "status": "error",
                "message": f"Unexpected error: {str(e)}"
            }

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
            cursor.close()
            conn.close()
            
            return {
                "status": "success",
                "memory_id": memory_id,
                "message": "Memory stored successfully"
            }
        except Error as e:
            print(f"Error storing memory: {e}")
            if conn:
                conn.close()
            return {
                "status": "error",
                "message": f"Failed to store memory: {str(e)}"
            }

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
            cursor.close()
            conn.close()
            
            return {
                "status": "success",
                "memories": memories,
                "count": len(memories)
            }
        except Error as e:
            print(f"Error retrieving memories: {e}")
            if conn:
                conn.close()
            return {
                "status": "error",
                "message": f"Failed to retrieve memories: {str(e)}"
            }
