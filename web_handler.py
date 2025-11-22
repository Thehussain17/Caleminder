from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import uuid
import mysql.connector
from mysql.connector import Error
import hashlib

class WebHandler:
    def __init__(self, orchestrator):
        self.app = Flask(__name__, template_folder='templates')
        
        self.app.secret_key = 'your_secret_key_here_change_in_production' # change in production
        self.orchestrator = orchestrator
        self.db_config = {
            'host': 'localhost',
            'user': 'root',
            'password': '', 
            'database': 'caleminder' 
        }
        self.setup_routes()

    def get_db_connection(self):
        """Create and return a database connection"""
        try:
            connection = mysql.connector.connect(**self.db_config)
            return connection
        except Error as e:
            # Print connection error for debugging
            print(f"Database connection error: {e}") 
            return None
        
    def setup_routes(self):
        # All route definitions remain in place within this method

        @self.app.route("/") 
        def auth_page():
            if session.get('authenticated'):
                return redirect(url_for('index'))
            # Note: auth.php is usually an HTML file in Flask. Ensure it's named 'auth.html' in 'templates'.
            return render_template('auth.php') 

        @self.app.route("/auth", methods=['POST']) 
        def authenticate():
            auth_type = request.form.get('auth_type')
            if auth_type == 'signIn':
                return self.handle_sign_in()
            elif auth_type == 'signUp':
                return self.handle_sign_up()
            else:
                return jsonify({'error': 'Invalid auth type'}), 400

        @self.app.route("/index.html") 
        def index():
            if not session.get('authenticated'):
                return redirect(url_for('auth_page'))
            # print(gs.var) # Removed reference to gs.var
            print("User is authenticated, serving index.html")
            return render_template('index.html')

        @self.app.route('/profile')
        def profile_page():
            if not session.get('authenticated'):
                return redirect(url_for('auth_page'))
            return render_template('profile.html')

        @self.app.route('/api/profile', methods=['GET'])
        def api_get_profile():
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'No user id in session'}), 400

            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500

            try:
                cur = conn.cursor(dictionary=True)
                cur.execute('SELECT id, firstname, lastname, username, email FROM users WHERE id = %s', (user_id,))
                user = cur.fetchone()
                cur.close()
                conn.close()
                if not user:
                    return jsonify({'error': 'User not found'}), 404
                return jsonify({'user': user}), 200
            except Error as e:
                print(f"Error fetching profile: {e}")
                return jsonify({'error': 'Failed to fetch profile'}), 500

        @self.app.route('/api/profile', methods=['POST'])
        def api_update_profile():
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'No user id in session'}), 400

            firstname = request.form.get('firstname', '').strip()
            lastname = request.form.get('lastname', '').strip()
            username = request.form.get('username', '').strip()
            password = request.form.get('password', '')

            if not all([firstname, lastname, username]):
                return jsonify({'error': 'firstname, lastname and username are required'}), 400

            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500

            try:
                cur = conn.cursor()
                cur.execute('SELECT id FROM users WHERE username = %s AND id != %s', (username, user_id))
                if cur.fetchone():
                    cur.close()
                    conn.close()
                    return jsonify({'error': 'Username already taken'}), 400

                if password:
                    password_hash = hashlib.md5(password.encode()).hexdigest()
                    cur.execute('UPDATE users SET firstname=%s, lastname=%s, username=%s, password=%s WHERE id=%s',
                                (firstname, lastname, username, password_hash, user_id))
                else:
                    cur.execute('UPDATE users SET firstname=%s, lastname=%s, username=%s WHERE id=%s',
                                (firstname, lastname, username, user_id))
                conn.commit()
                cur.close()
                conn.close()
                return jsonify({'success': True, 'message': 'Profile updated'}), 200
            except Error as e:
                print(f"Error updating profile: {e}")
                return jsonify({'error': 'Failed to update profile: ' + str(e)}), 500

        @self.app.route('/api/delete-account', methods=['POST'])
        def api_delete_account():
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'No user id in session'}), 400

            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500

            try:
                cur = conn.cursor()
                cur.execute('DELETE FROM users WHERE id = %s', (user_id,))
                conn.commit()
                cur.close()
                conn.close()

                print(f"User account deleted: id={user_id}")
                session.clear()
                return jsonify({'success': True, 'message': 'Account deleted successfully'}), 200
            except Error as e:
                print(f"Error deleting account: {e}")
                return jsonify({'error': 'Failed to delete account: ' + str(e)}), 500

        @self.app.route('/api/upcoming-tasks', methods=['GET'])
        def api_get_upcoming_tasks():
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'No user id in session'}), 400

            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500

            try:
                cur = conn.cursor(dictionary=True)
                query = """
                    SELECT 
                        st.id, st.user_id, st.task_type, st.task_title, st.task_description, 
                        st.scheduled_time, st.status, st.retry_count, st.created_at, 
                        u.firstname, u.lastname, u.username, u.email
                    FROM scheduled_tasks st
                    JOIN users u ON st.user_id = u.id
                    WHERE st.user_id = %s AND st.status IN ('pending', 'scheduled')
                    ORDER BY st.scheduled_time ASC
                """
                cur.execute(query, (user_id,))
                tasks = cur.fetchall()
                cur.close()
                conn.close()

                # Convert TIMESTAMP to string for JSON serialization
                for task in tasks:
                    if task['scheduled_time']:
                        task['scheduled_time'] = task['scheduled_time'].isoformat()
                    if task['created_at']:
                        task['created_at'] = task['created_at'].isoformat()

                return jsonify({'tasks': tasks}), 200
            except Error as e:
                print(f"Error fetching tasks: {e}")
                return jsonify({'error': 'Failed to fetch tasks: ' + str(e)}), 500

        @self.app.route('/api/upcoming-tasks', methods=['POST'])
        def api_create_task():
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'No user id in session'}), 400

            task_type = request.form.get('task_type', '').strip()
            task_title = request.form.get('task_title', '').strip()
            task_description = request.form.get('task_description', '').strip()
            scheduled_time = request.form.get('scheduled_time', '').strip()

            if not all([task_type, task_title, scheduled_time]):
                return jsonify({'error': 'task_type, task_title and scheduled_time are required'}), 400

            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500

            try:
                cur = conn.cursor()
                insert_query = """
                    INSERT INTO scheduled_tasks 
                    (user_id, task_type, task_title, task_description, scheduled_time, status)
                    VALUES (%s, %s, %s, %s, %s, 'pending')
                """
                cur.execute(insert_query, (user_id, task_type, task_title, task_description, scheduled_time))
                conn.commit()
                task_id = cur.lastrowid
                
                cur.close()
                conn.close()

                return jsonify({'success': True, 'task_id': task_id, 'message': 'Task created successfully'}), 200
            except Error as e:
                print(f"Error creating task: {type(e).__name__} - {e}")
                conn.close()
                return jsonify({'error': f'Failed to create task: {str(e)}'}), 500

        @self.app.route("/chat", methods=['POST'])
        def chat():
            user_id = request.form.get("user_id", "hackathon_user")
            user_message = request.form.get("message", "")
            image_file = request.files.get("image")
            
            temp_path = None
            message = {
                'user_id': user_id,
                'text': user_message,
                'image_path': None,
                'image_mime_type': None
            }
            
            try:
                if image_file and image_file.filename != '':
                    temp_dir = 'tmp'
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    
                    filename = f"{uuid.uuid4()}{os.path.splitext(image_file.filename)[1]}"
                    temp_path = os.path.join(temp_dir, filename)
                    image_file.save(temp_path)
                    
                    message['image_path'] = temp_path
                    message['image_mime_type'] = image_file.mimetype

                response_text = self.orchestrator.handle_message(message)
                return jsonify({'response': response_text})

            except Exception as e:
                print(f"An error occurred in the web handler: {e}")
                return jsonify({'response': 'Sorry, a critical error occurred on the server.'}), 500
            finally:
                # Clean up the temporary file
                if temp_path and os.path.exists(temp_path):
                    os.remove(temp_path)

        @self.app.route('/api/memories', methods=['GET'])
        def api_get_memories():
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401
            
            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'No user id in session'}), 400

            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500

            try:
                cur = conn.cursor(dictionary=True)
                query = """
                    SELECT id, user_id, category, fact_content, confidence_score
                    FROM user_memories
                    WHERE user_id = %s
                    ORDER BY category, id DESC
                """
                cur.execute(query, (user_id,))
                memories = cur.fetchall()
                cur.close()
                conn.close()

                return jsonify({'memories': memories}), 200
            except Error as e:
                print(f"Error fetching memories: {e}")
                return jsonify({'error': 'Failed to fetch memories: ' + str(e)}), 500

        @self.app.route('/api/memories', methods=['POST'])
        def api_create_memory():
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'No user id in session'}), 400

            category = request.form.get('category', '').strip()
            fact_content = request.form.get('fact_content', '').strip()
            confidence_score = request.form.get('confidence_score', 1.0)

            if not all([category, fact_content]):
                return jsonify({'error': 'category and fact_content are required'}), 400

            try:
                confidence_score = float(confidence_score)
                if not (0 <= confidence_score <= 1):
                    return jsonify({'error': 'confidence_score must be between 0 and 1'}), 400
            except (ValueError, TypeError):
                return jsonify({'error': 'confidence_score must be a valid number'}), 400

            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500

            try:
                cur = conn.cursor()
                insert_query = """
                    INSERT INTO user_memories 
                    (user_id, category, fact_content, confidence_score)
                    VALUES (%s, %s, %s, %s)
                """
                cur.execute(insert_query, (user_id, category, fact_content, confidence_score))
                conn.commit()
                memory_id = cur.lastrowid
                
                cur.close()
                conn.close()

                return jsonify({'success': True, 'memory_id': memory_id, 'message': 'Memory stored successfully'}), 200
            except Error as e:
                print(f"Error storing memory: {type(e).__name__} - {e}")
                conn.close()
                return jsonify({'error': f'Failed to store memory: {str(e)}'}), 500

        @self.app.route('/api/memories/<int:memory_id>', methods=['DELETE'])
        def api_delete_memory(memory_id):
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'No user id in session'}), 400

            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500

            try:
                cur = conn.cursor()
                cur.execute('SELECT user_id FROM user_memories WHERE id = %s', (memory_id,))
                result = cur.fetchone()
                
                if not result or result[0] != user_id:
                    cur.close()
                    conn.close()
                    return jsonify({'error': 'Memory not found or unauthorized'}), 404

                cur.execute('DELETE FROM user_memories WHERE id = %s', (memory_id,))
                conn.commit()
                
                cur.close()
                conn.close()

                return jsonify({'success': True, 'message': 'Memory deleted successfully'}), 200
            except Error as e:
                print(f"Error deleting memory: {e}")
                return jsonify({'error': 'Failed to delete memory: ' + str(e)}), 500

        @self.app.route('/api/memories/query', methods=['POST'])
        def api_query_memories():
            if not session.get('authenticated'):
                return jsonify({'error': 'Not authenticated'}), 401

            user_id = session.get('user_id')
            if not user_id:
                return jsonify({'error': 'No user id in session'}), 400

            category = request.form.get('category', '').strip()

            if not category:
                return jsonify({'error': 'category is required'}), 400

            conn = self.get_db_connection()
            if not conn:
                return jsonify({'error': 'Database connection failed'}), 500

            try:
                cur = conn.cursor(dictionary=True)
                query = """
                    SELECT fact_content, confidence_score
                    FROM user_memories
                    WHERE user_id = %s AND category = %s
                    ORDER BY confidence_score DESC
                """
                cur.execute(query, (user_id, category))
                memories = cur.fetchall()
                cur.close()
                conn.close()

                return jsonify({'memories': memories}), 200
            except Error as e:
                print(f"Error querying memories: {e}")
                return jsonify({'error': 'Failed to query memories: ' + str(e)}), 500
            
    def handle_sign_in(self):
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')

        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        connection = self.get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = None
        try:
            cursor = connection.cursor(dictionary=True)
            password_hash = hashlib.md5(password.encode()).hexdigest()
            
            query = "SELECT id, email, firstname FROM users WHERE email = %s AND password = %s"
            cursor.execute(query, (email, password_hash))
            user = cursor.fetchone()
            
            if user:
                session['authenticated'] = True
                session['email'] = user['email']
                session['user_id'] = user['id']
                session['firstname'] = user['firstname']
                print(f"User logged in successfully: ID={session['user_id']}")
                return jsonify({'success': True, 'message': 'Login successful'}), 200
            else:
                print(f"Login failed for email: {email}")
                return jsonify({'error': 'Incorrect email or password'}), 401
                
        except Error as e:
            print(f"Database error during login: {type(e).__name__} - {e}")
            return jsonify({'error': f'Login failed: {str(e)}'}), 500
        except Exception as e:
            print(f"Unexpected error during login: {type(e).__name__} - {e}")
            return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()

    def handle_sign_up(self):
        firstname = request.form.get('firstname', '').strip()
        lastname = request.form.get('lastname', '').strip()
        username = request.form.get('username', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not all([firstname, lastname, username, email, password]):
            return jsonify({'error': 'All fields are required'}), 400
        
        connection = self.get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        cursor = None
        try:
            cursor = connection.cursor()
            
            # Check if email already exists
            cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
            if cursor.fetchone():
                return jsonify({'error': 'Email already registered'}), 400
            
            # Check if username already exists
            cursor.execute("SELECT id FROM users WHERE username = %s", (username,))
            if cursor.fetchone():
                return jsonify({'error': 'Username already taken'}), 400
            
            # Hash password
            password_hash = hashlib.md5(password.encode()).hexdigest()
            
            # Insert new user
            insert_query = """INSERT INTO users (firstname, lastname, username, email, password) 
                              VALUES (%s, %s, %s, %s, %s)"""
            cursor.execute(insert_query, (firstname, lastname, username, email, password_hash))
            connection.commit()
            
            print(f"User registered successfully: {email}")
            
            # Set session variables
            session['authenticated'] = True
            session['email'] = email
            session['firstname'] = firstname
            session['user_id'] = cursor.lastrowid
            
            return jsonify({'success': True, 'message': 'Registration successful'}), 200
            
        except Error as e:
            print(f"Database error during registration: {type(e).__name__} - {e}")
            return jsonify({'error': f'Registration failed: {str(e)}'}), 500
        except Exception as e:
            print(f"Unexpected error during registration: {type(e).__name__} - {e}")
            return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
        finally:
            if cursor:
                cursor.close()
            if connection and connection.is_connected():
                connection.close()
        
    def start(self):
        print("Starting Flask server. Open http://127.0.0.1:5000 in your browser.")
        # Removed debug=True for production style, but left it for ease of development.
        self.app.run(host='0.0.0.0', port=5000, debug=True)