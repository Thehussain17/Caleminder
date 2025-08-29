from orchestrator import Orchestrator
from web_handler import WebHandler

if __name__ == "__main__":
    try:
        orchestrator = Orchestrator()
        web_handler = WebHandler(orchestrator)
        web_handler.start()
    except Exception as e:
        print(f"FATAL: Application failed to start. Error: {e}")