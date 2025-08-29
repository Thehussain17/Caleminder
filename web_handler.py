# web_handler.py
from flask import Flask, request, jsonify, render_template

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
            user_message = request.form.get("message", "")
            image_file = request.files.get("image")
            message_obj = {"user_id": "hackathon_user", "text": user_message, "image": image_file}
            ai_response = self.orchestrator.handle_message(message_obj)
            return jsonify({"response": ai_response})

    def start(self):
        print("Starting Flask server. Open http://12.0.0.1:5000 in your browser.")
        self.app.run(host='0.0.0.0', port=5000, debug=True)
