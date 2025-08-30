# web_handler.py
from flask import Flask, request, jsonify, render_template
import os
import uuid

class WebHandler:
    def __init__(self, orchestrator):
        self.app = Flask(__name__, template_folder='templates')
        self.orchestrator = orchestrator
        self.setup_routes()

    def setup_routes(self):
        @self.app.route("/")
        def index():
            return render_template('index.html')

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
        print("Starting Flask server. Open http://12.0.0.1:5000 in your browser.")
        self.app.run(host='0.0.0.0', port=5000, debug=True)
