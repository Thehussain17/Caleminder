from flask import Flask, request, jsonify, render_template, redirect, url_for, session
import os
import uuid
import mysql.connector
from mysql.connector import Error
import hashlib

class WebHandler:
    def __init__(self, orchestrator):
        self.app = Flask(__name__, template_folder='templates')
        self.app.secret_key = 'your_secret_key_here_change_in_production'
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
            print(f"Database connection error: {e}")
            return None

    def setup_routes(self):
        @self.app.route("/")  # Entry point - Auth page
        def auth_page():
            # Redirect to login if already authenticated
            if session.get('authenticated'):
                return redirect(url_for('index'))
            return render_template('auth.php')

        @self.app.route("/auth", methods=['POST'])  # Authentication endpoint
        def authenticate():
            """Handle authentication (sign in and sign up)"""
            auth_type = request.form.get('auth_type')
            
            if auth_type == 'signIn':
                return self.handle_sign_in()
            elif auth_type == 'signUp':
                return self.handle_sign_up()
            else:
                return jsonify({'error': 'Invalid auth type'}), 400

        @self.app.route("/index.html")  # Main app page (protected) (Changes by risbern)
        def index():
            # Check if user is authenticated
            if not session.get('authenticated'):
                return redirect(url_for('auth_page'))
            # This is the page users see after logging in
            return render_template('index.html')

        @self.app.route('/profile')
        def profile_page():
            # Protected profile page
            if not session.get('authenticated'):
                return redirect(url_for('auth_page'))
            return render_template('profile.html')

        @self.app.route('/api/profile', methods=['GET'])
        def api_get_profile():
            """Return current user profile as JSON (requires Flask session)"""
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
            """Update current user profile (name, username, optional password)"""
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
                # Check username uniqueness (exclude current user)
                cur.execute('SELECT id FROM users WHERE username = %s AND id != %s', (username, user_id))
                if cur.fetchone():
                    cur.close()
                    conn.close()
                    return jsonify({'error': 'Username already taken'}), 400

                if password:
                    # Hash password using MD5 to match existing scheme (recommend upgrading later)
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

        @self.app.route("/chat", methods=['POST'])
        def chat():
            user_id = request.form.get("user_id", "hackathon_user")
            user_message = request.form.get("message", "")
            image_file = request.files.get("image")
            # message_obj = {"user_id": "hackathon_user", "text": user_message, "image": image_file}
            # # ai_response = self.orchestrator.handle_message(message_obj)
            temp_path = None
            message = {
                'user_id': user_id,
                'text': user_message,
                'image_path': None,
                'image_mime_type': None
            }
            
            try:
                # --- NEW LOGIC: Save the file temporarily ---
                if image_file and image_file.filename != '':
                    # Create a temporary directory if it doesn't exist
                    temp_dir = 'tmp'
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    
                    # Create a secure, unique filename and path
                    filename = f"{uuid.uuid4()}{os.path.splitext(image_file.filename)[1]}"
                    temp_path = os.path.join(temp_dir, filename)
                    image_file.save(temp_path)
                    
                    # Update the message with the path and mime type
                    message['image_path'] = temp_path
                    message['image_mime_type'] = image_file.mimetype

                response_text = self.orchestrator.handle_message(message)
                return jsonify({'response': response_text})


            except Exception as e:
                print(f"An error occurred in the web handler: {e}")
                return jsonify({'response': 'Sorry, a critical error occurred on the server.'}), 500

    def handle_sign_in(self):
        """Handle user sign in"""
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400
        
        connection = self.get_db_connection()
        if not connection:
            return jsonify({'error': 'Database connection failed'}), 500
        
        try:
            cursor = connection.cursor(dictionary=True)
            password_hash = hashlib.md5(password.encode()).hexdigest()
            
            query = "SELECT id, email, firstname FROM users WHERE email = %s AND password = %s"
            cursor.execute(query, (email, password_hash))
            user = cursor.fetchone()
            
            cursor.close()
            connection.close()
            
            if user:
                # Set session variables
                session['authenticated'] = True
                session['email'] = user['email']
                session['user_id'] = user['id']
                session['firstname'] = user['firstname']
                
                print(f"User logged in successfully: {email}")
                
                # Return success JSON response
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
            try:
                cursor.close()
                connection.close()
            except:
                pass

    def handle_sign_up(self):
        """Handle user sign up"""
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
        
        try:
            cursor = connection.cursor()
            
            # Check if email already exists
            check_query = "SELECT id FROM users WHERE email = %s"
            cursor.execute(check_query, (email,))
            if cursor.fetchone():
                cursor.close()
                connection.close()
                return jsonify({'error': 'Email already registered'}), 400
            
            # Check if username already exists
            check_query = "SELECT id FROM users WHERE username = %s"
            cursor.execute(check_query, (username,))
            if cursor.fetchone():
                cursor.close()
                connection.close()
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
            
            cursor.close()
            connection.close()
            
            # Return success JSON response
            return jsonify({'success': True, 'message': 'Registration successful'}), 200
            
        except Error as e:
            print(f"Database error during registration: {type(e).__name__} - {e}")
            print(f"Form data - firstname: {firstname}, lastname: {lastname}, username: {username}, email: {email}")
            return jsonify({'error': f'Registration failed: {str(e)}'}), 500
        except Exception as e:
            print(f"Unexpected error during registration: {type(e).__name__} - {e}")
            return jsonify({'error': f'Unexpected error: {str(e)}'}), 500
        finally:
            try:
                cursor.close()
                connection.close()
            except:
                pass

        @self.app.route("/chat", methods=['POST'])
        def chat():
            user_id = request.form.get("user_id", "hackathon_user")
            user_message = request.form.get("message", "")
            image_file = request.files.get("image")
            # message_obj = {"user_id": "hackathon_user", "text": user_message, "image": image_file}
            # # ai_response = self.orchestrator.handle_message(message_obj)
            temp_path = None
            message = {
                'user_id': user_id,
                'text': user_message,
                'image_path': None,
                'image_mime_type': None
            }
            
            try:
                # --- NEW LOGIC: Save the file temporarily ---
                if image_file and image_file.filename != '':
                    # Create a temporary directory if it doesn't exist
                    temp_dir = 'tmp'
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    
                    # Create a secure, unique filename and path
                    filename = f"{uuid.uuid4()}{os.path.splitext(image_file.filename)[1]}"
                    temp_path = os.path.join(temp_dir, filename)
                    image_file.save(temp_path)
                    
                    # Update the message with the path and mime type
                    message['image_path'] = temp_path
                    message['image_mime_type'] = image_file.mimetype

                response_text = self.orchestrator.handle_message(message)
                return jsonify({'response': response_text})


            except Exception as e:
                print(f"An error occurred in the web handler: {e}")
                return jsonify({'response': 'Sorry, a critical error occurred on the server.'}), 500
            
            

    def start(self):
        print("Starting Flask server. Open http://127.0.0.1:5000 in your browser.")
        self.app.run(host='0.0.0.0', port=5000, debug=True)