# config.py
import os
from dotenv import load_dotenv
load_dotenv()

# --- Core API Keys ---
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "YOUR_GEMINI_API_KEY_HERE")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_API_TOKEN")

# --- Google OAuth (Web Application) ---
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")

# --- Firebase ---
FIREBASE_CREDENTIALS_PATH = os.getenv("FIREBASE_CREDENTIALS_PATH", "firebase_service_account.json")

# --- App Configuration ---
APP_URL = os.getenv("APP_URL", "http://127.0.0.1:5000")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:5173")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "dev-secret-key-change-in-production")
ENVIRONMENT = os.getenv("ENVIRONMENT", "development")
