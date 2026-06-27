# web_handler.py
import os
import json
import uuid
import requests as http_requests
from flask import Flask, request, jsonify, session, redirect, url_for, abort
from flask_cors import CORS
from google_auth_oauthlib.flow import Flow
from werkzeug.middleware.proxy_fix import ProxyFix
import config

# Allow OAuth over HTTP for local development only
if config.ENVIRONMENT == "development":
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'


class WebHandler:
    def __init__(self, orchestrator):
        self.app = Flask(__name__)
        self.app.secret_key = config.FLASK_SECRET_KEY

        # Trust proxy headers (needed behind nginx, Cloud Run, etc.)
        self.app.wsgi_app = ProxyFix(self.app.wsgi_app, x_for=1, x_proto=1, x_host=1)

        # CORS for React dev server and production frontend
        cors_origins = ["http://localhost:5173", "http://127.0.0.1:5173"]
        if config.FRONTEND_URL and config.FRONTEND_URL not in cors_origins:
            cors_origins.append(config.FRONTEND_URL)
        CORS(self.app, supports_credentials=True, origins=cors_origins)

        self.orchestrator = orchestrator

        # Import UserDB from firebase_db
        from firebase_db import UserDB
        self.user_db = UserDB()

        # OAuth Configuration (Web Application type)
        self.client_config = {
            "web": {
                "client_id": config.GOOGLE_CLIENT_ID,
                "client_secret": config.GOOGLE_CLIENT_SECRET,
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
            "https://www.googleapis.com/auth/drive",
            "openid",
        ]

        self.setup_routes()

    def _get_redirect_uri(self):
        return f"{config.APP_URL}/api/auth/callback"

    def setup_routes(self):

        # ---- Auth Status ----
        @self.app.route("/api/auth/status")
        def auth_status():
            if 'user_id' not in session:
                return jsonify({'authenticated': False}), 401
            return jsonify({
                'authenticated': True,
                'user': {
                    'id': session['user_id'],
                    'name': session.get('user_name'),
                    'picture': session.get('user_picture'),
                }
            })

        # ---- OAuth Flow ----
        @self.app.route("/api/auth/google")
        def google_auth():
            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES,
                redirect_uri=self._get_redirect_uri(),
            )
            authorization_url, state = flow.authorization_url(
                access_type='offline',
                include_granted_scopes='true',
                prompt='select_account consent',
            )
            session['state'] = state
            return redirect(authorization_url)

        @self.app.route("/api/auth/callback")
        def auth_callback():
            state = session.get('state')
            if not state:
                return redirect(f"{config.FRONTEND_URL}/login")

            flow = Flow.from_client_config(
                self.client_config,
                scopes=self.SCOPES,
                state=state,
                redirect_uri=self._get_redirect_uri(),
            )
            try:
                flow.fetch_token(authorization_response=request.url)
            except Exception as e:
                print(f"OAuth token exchange failed: {e}")
                return redirect(f"{config.FRONTEND_URL}/login")

            credentials = flow.credentials

            # Fetch user info
            user_info_resp = http_requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {credentials.token}'},
            )
            user_info = user_info_resp.json()

            user_id = user_info['id']
            session['user_id'] = user_id
            session['user_name'] = user_info.get('name')
            session['user_picture'] = user_info.get('picture')

            creds_json = credentials.to_json()
            session['credentials_json'] = creds_json

            try:
                self.user_db.save_user(user_info, creds_json)
                print(f"Successfully saved user {user_id} to Firebase")
            except Exception as e:
                print(f"WARNING: Failed to save user to Firebase: {e}")
                import traceback
                traceback.print_exc()

            # Redirect to React app
            return redirect(f"{config.FRONTEND_URL}/")

        @self.app.route("/api/auth/logout", methods=['POST'])
        def logout():
            session.clear()
            return jsonify({'status': 'ok'})

        # ---- Chat Sessions ----
        @self.app.route("/api/sessions")
        def list_sessions():
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            sessions = self.user_db.get_user_sessions(session['user_id'])
            return jsonify(sessions)

        @self.app.route("/api/sessions", methods=['POST'])
        def new_chat():
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            session_id = self.user_db.create_chat_session(session['user_id'])
            return jsonify({'session_id': session_id})

        @self.app.route("/api/chat/<session_id>", methods=['GET'])
        def get_chat(session_id):
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401

            chat_session = self.user_db.get_session(session_id)
            if not chat_session or chat_session['user_id'] != session['user_id']:
                return jsonify({'error': 'Not found'}), 404

            history = self.user_db.load_chat_history(session_id)
            # Serialize history for JSON response
            messages = []
            for item in history:
                for part in item.parts:
                    if part.text and part.text != '[FILE UPLOADED]':
                        messages.append({
                            'role': item.role,
                            'text': part.text,
                        })
            return jsonify({'session': chat_session, 'messages': messages})

        @self.app.route("/api/chat/<session_id>", methods=['DELETE'])
        def delete_chat(session_id):
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401

            chat_session = self.user_db.get_session(session_id)
            if not chat_session or chat_session['user_id'] != session['user_id']:
                return jsonify({'error': 'Not found'}), 404

            self.user_db.delete_session(session_id)
            return jsonify({'success': True})

        @self.app.route("/api/chat/<session_id>", methods=['POST'])
        def send_message(session_id):
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401

            chat_session = self.user_db.get_session(session_id)
            if not chat_session or chat_session['user_id'] != session['user_id']:
                return jsonify({'error': 'Not found'}), 404

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

            # Get credentials (Firebase with session fallback)
            credentials_json = self.user_db.get_user_credentials(session['user_id'])
            if not credentials_json:
                credentials_json = session.get('credentials_json')

            current_history = self.user_db.load_chat_history(session_id)

            message = {
                'user_id': session['user_id'],
                'text': user_message,
                'image_path': temp_path,
                'image_mime_type': mime_type,
                'credentials': credentials_json,
                'history': current_history,
            }

            result = self.orchestrator.handle_message(message)

            self.user_db.save_chat_history(session_id, result['new_history'])

            # Auto-title first message
            if len(current_history) == 0:
                new_title = (user_message[:30] + '..') if len(user_message) > 30 else user_message
                if not new_title and image_file:
                    new_title = "Image Analysis"
                if new_title:
                    self.user_db.update_session_title(session_id, new_title)

            return jsonify({'response': result['text']})

        # ---- Widget Data Endpoints ----
        @self.app.route("/api/calendar/upcoming")
        def upcoming_events():
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            # Return empty for now — will be populated by actual calendar data
            return jsonify({'events': []})

        @self.app.route("/api/tasks/today")
        def today_tasks():
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            return jsonify({'tasks': []})

        @self.app.route("/api/user/stats")
        def user_stats():
            if 'user_id' not in session:
                return jsonify({'error': 'Unauthorized'}), 401
            sessions_count = len(self.user_db.get_user_sessions(session['user_id']))
            return jsonify({
                'name': session.get('user_name'),
                'picture': session.get('user_picture'),
                'sessions_count': sessions_count,
            })

    def start(self):
        print("Starting Flask API server...")
        if config.ENVIRONMENT == "development":
            self.app.run(host='0.0.0.0', port=5000, debug=True)
        else:
            self.app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
