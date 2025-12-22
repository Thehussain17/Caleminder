# web_handler.py
import os
import json
import uuid
import pathlib
import requests
from flask import Flask, request, jsonify, render_template, session, redirect, url_for, abort
from google_auth_oauthlib.flow import Flow
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from user_database import UserDB
from orchestrator import Orchestrator

# Allow OAuth over HTTP for local testing/dev. In production, this should be set to 1.
os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

class WebHandler:
    def __init__(self, orchestrator):
        self.app = Flask(__name__, template_folder='templates')
        self.app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_key_for_dev")
        self.orchestrator = orchestrator
        self.user_db = UserDB()

        # OAuth Configuration
        self.GOOGLE_CLIENT_ID = os.environ.get("GOOGLE_CLIENT_ID")
        self.GOOGLE_CLIENT_SECRET = os.environ.get("GOOGLE_CLIENT_SECRET")

        self.client_config = {
            "web": {
                "client_id": self.GOOGLE_CLIENT_ID,
                "client_secret": self.GOOGLE_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            }
        }

        self.SCOPES = [
            "https://www.googleapis.com/auth/userinfo.profile",
            "https://www.googleapis.com/auth/userinfo.email",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/tasks",
            "https://www.googleapis.com/auth/contacts",
            "https://www.googleapis.com/auth/gmail.send",
            "openid"
        ]

        self.setup_routes()

    def setup_routes(self):

        @self.app.route("/")
        def index():
            if 'user_id' not in session:
                return redirect(url_for('login_page'))

            user_sessions = self.user_db.get_user_sessions(session['user_id'])
            if user_sessions:
                return redirect(url_for('chat_page', session_id=user_sessions[0]['id']))
            else:
                new_id = self.user_db.create_chat_session(session['user_id'])
                return redirect(url_for('chat_page', session_id=new_id))

        @self.app.route("/login")
        def login_page():
            return render_template('login.html')

        @self.app.route("/auth/google")
        def google_auth():
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES,
                redirect_uri=url_for('auth_callback', _external=True)
            )

            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='consent'
            )

            session['state'] = state
            return redirect(authorization_url)

        @self.app.route("/auth/callback")
        def auth_callback():
            state = session.get('state')
            if not state:
                 return redirect(url_for('login_page'))

            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES,
                state=state,
                redirect_uri=url_for('auth_callback', _external=True)
            )

            flow.fetch_token(authorization_response=request.url)

            credentials = flow.credentials

            user_info_resp = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {credentials.token}'}
            )
            user_info = user_info_resp.json()

            user_id = user_info['id']
            session['user_id'] = user_id
            session['user_name'] = user_info.get('name')
            session['user_picture'] = user_info.get('picture')

            creds_json = credentials.to_json()
            self.user_db.save_user(user_info, creds_json)

            return redirect(url_for('index'))

        @self.app.route("/logout")
        def logout():
            session.clear()
            return redirect(url_for('login_page'))

        @self.app.route("/sessions")
        def list_sessions():
            if 'user_id' not in session:
                return jsonify([]), 401
            sessions = self.user_db.get_user_sessions(session['user_id'])
            return jsonify(sessions)

        @self.app.route("/new_chat", methods=['POST'])
        def new_chat():
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401

            session_id = self.user_db.create_chat_session(session['user_id'])
            return jsonify({'session_id': session_id})

        @self.app.route("/chat/<session_id>", methods=['GET', 'POST'])
        def chat_page(session_id):
            if 'user_id' not in session:
                return redirect(url_for('login_page'))

            chat_session = self.user_db.get_session(session_id)
            if not chat_session or chat_session['user_id'] != session['user_id']:
                return abort(404)

            if request.method == 'GET':
                history = self.user_db.load_chat_history(session_id)
                user = {
                    'name': session.get('user_name'),
                    'picture': session.get('user_picture')
                }
                return render_template('chat.html', history=history, user=user)

            elif request.method == 'POST':
                user_message = request.form.get("message", "")
                image_file = request.files.get("image")

                temp_path = None
                mime_type = None

                if image_file and image_file.filename != '':
                    temp_dir = 'tmp'
                    if not os.path.exists(temp_dir):
                        os.makedirs(temp_dir)
                    filename = f"{uuid.uuid4()}{os.path.splitext(image_file.filename)[1]}"
                    temp_path = os.path.join(temp_dir, filename)
                    image_file.save(temp_path)
                    mime_type = image_file.mimetype

                credentials_json = self.user_db.get_user_credentials(session['user_id'])
                current_history = self.user_db.load_chat_history(session_id)

                message = {
                    'user_id': session['user_id'],
                    'text': user_message,
                    'image_path': temp_path,
                    'image_mime_type': mime_type,
                    'credentials': credentials_json,
                    'history': current_history
                }

                result = self.orchestrator.handle_message(message)

                self.user_db.save_chat_history(session_id, result['new_history'])

                if len(current_history) == 0:
                    new_title = (user_message[:30] + '..') if len(user_message) > 30 else user_message
                    if not new_title and image_file:
                        new_title = "Image Analysis"
                    if new_title:
                        self.user_db.update_session_title(session_id, new_title)

                return jsonify({'response': result['text']})

    def start(self):
        print("Starting Flask server...")
        self.app.run(host='0.0.0.0', port=5000, debug=True)
