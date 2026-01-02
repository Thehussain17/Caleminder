# web_handler.py
import os
import json
import uuid
import requests
from flask import Flask, request, jsonify, session, redirect, url_for, abort, send_from_directory
from google_auth_oauthlib.flow import Flow
from user_database import UserDB
from orchestrator import Orchestrator

os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'

def serialize_history(history):
    """
    Convert a list of google.genai.types.Content objects to a list of dicts.
    """
    serialized = []
    for content in history:
        item = {'role': content.role, 'parts': []}
        for part in content.parts:
            p_dict = {}
            if part.text:
                p_dict['text'] = part.text
            if part.file_data:
                # We can't easily send the file data back if it's not stored or valid,
                # but our history saves '[FILE UPLOADED]' text marker often.
                # If we have real file_data object, we might just indicate it.
                p_dict['file_data'] = True
            if part.function_call:
                p_dict['function_call'] = {'name': part.function_call.name, 'args': dict(part.function_call.args)}
            if part.function_response:
                p_dict['function_response'] = {'name': part.function_response.name, 'response': part.function_response.response}
            item['parts'].append(p_dict)
        serialized.append(item)
    return serialized

class WebHandler:
    def __init__(self, orchestrator):
        self.static_folder = os.path.join(os.getcwd(), 'frontend', 'dist')
        self.app = Flask(__name__, static_folder=self.static_folder, static_url_path='/')
        self.app.secret_key = os.environ.get("FLASK_SECRET_KEY", "super_secret_key_for_dev")
        self.orchestrator = orchestrator
        self.user_db = UserDB()

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

        # --- API Routes ---

        @self.app.route("/api/auth/google")
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

        @self.app.route("/api/auth/callback")
        def auth_callback():
            state = session.get('state')
            if not state:
                 return redirect('/')

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

            return redirect('/')

        @self.app.route("/api/logout")
        def logout():
            session.clear()
            return redirect('/')

        @self.app.route("/api/sessions")
        def list_sessions():
            if 'user_id' not in session:
                return jsonify([]), 401
            sessions = self.user_db.get_user_sessions(session['user_id'])
            return jsonify(sessions)

        @self.app.route("/api/new_chat", methods=['POST'])
        def new_chat():
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401

            session_id = self.user_db.create_chat_session(session['user_id'])
            return jsonify({'session_id': session_id})

        @self.app.route("/api/chat/<session_id>", methods=['GET', 'POST'])
        def chat_page(session_id):
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401

            chat_session = self.user_db.get_session(session_id)
            if not chat_session or chat_session['user_id'] != session['user_id']:
                return jsonify({'error': 'Not found'}), 404

            if request.method == 'GET':
                raw_history = self.user_db.load_chat_history(session_id)
                # Serialize history
                history = serialize_history(raw_history)

                user = {
                    'name': session.get('user_name'),
                    'picture': session.get('user_picture')
                }
                return jsonify({'history': history, 'user': user})

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

        # --- Static Serving ---
        @self.app.route("/", defaults={'path': ''})
        @self.app.route("/<path:path>")
        def serve(path):
            if path != "" and os.path.exists(os.path.join(self.app.static_folder, path)):
                return send_from_directory(self.app.static_folder, path)
            else:
                return send_from_directory(self.app.static_folder, 'index.html')

    def start(self):
        print("Starting Flask server...")
        self.app.run(host='0.0.0.0', port=5000, debug=True)
