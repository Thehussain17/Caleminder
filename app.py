from orchestrator import Orchestrator
from web_handler import WebHandler

# Create the app-level objects for gunicorn compatibility
orchestrator = Orchestrator()
web_handler = WebHandler(orchestrator)
application = web_handler.app  # gunicorn entry point: "app:application"

if __name__ == "__main__":
    try:
        web_handler.start()
    except Exception as e:
        print(f"FATAL: Application failed to start. Error: {e}")