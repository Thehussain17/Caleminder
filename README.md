Caleminder AI: Your Proactive Executive Partner
Caleminder is a sophisticated, multi-platform AI assistant designed to function as a proactive executive partner. It integrates deeply with a user's Google Workspace (Calendar, Tasks, Contacts, Gmail) to manage their schedule, tasks, and communications with an intelligent and assistive persona

Core Features
Conversational Interface: Interact with the assistant via a clean web UI or directly through Telegram using natural language.

Multi-Modal Scheduling: Create events from simple text commands ("Schedule a meeting...") or by uploading an image/PDF of a timetable.

Advanced Calendar Management:

Handles recurring events (RRULE generation).

Intelligently color-codes events by category (Work, Personal, Urgent, etc.).

Automatically generates Google Meet links for online meetings.

Finds and removes events based on natural language queries.

Proactive Task Management:

Creates tasks and intelligently files them into relevant categories (e.g., 'Work', 'Personal'), creating new lists on the fly.

Delivers a "Morning Briefing" summarizing the user's tasks for the day upon their first interaction.

Intelligent Communication:

Finds contacts in the user's Google Contacts.

Composes and sends email notifications for new meetings.

Persistent Memory & Personalization:

Remembers user details (name, preferences) across sessions using a local SQLite database.

Actively learns user preferences and uses them to personalize interactions and scheduling decisions.

Robust Authentication: Implements a secure, professional web-based OAuth 2.0 flow for user authorization, suitable for a production environment.

Architecture Overview
The application is built on a modular, object-oriented architecture designed for scalability and maintainability.

Communication Layer (web_handler.py, telegram_handler.py): The "face" of the application. These modules handle all platform-specific interactions and are completely decoupled from the core logic.

Orchestrator (orchestrator.py): The "brain." This central class manages the conversational flow, interprets user intent, and decides which tools to use by interacting with the Gemini API.

Tool Layer (calendar_tools.py, todo_tools.py, etc.): The "hands." Each class is a specialized module responsible for interacting with a specific external API (Google Calendar, Tasks, etc.).

Persistence Layer (user_database.py): The "memory." This module manages the SQLite database for storing user profiles and conversation history.

Authentication (auth_manager.py): A centralized manager for handling the complex, user-specific OAuth 2.0 flow for all Google APIs.

Tech Stack
Backend: Python

AI Model: Google Gemini 2.5 Flash

APIs: Google Workspace (Calendar, Tasks, People, Gmail)

Web Framework: Flask

Telegram Bot: python-telegram-bot

Database: SQLite

Date/Time Parsing: python-dateutil, tzlocal

Setup and Installation
Follow these steps precisely to get the application running.

1. Prerequisites
Python 3.9+

Git

2. Google Cloud Project Setup
This is the most critical step.

Go to the Google Cloud Console.

Create a new project.

In the project dashboard, go to APIs & Services > Library.

Search for and Enable the following APIs:

Google Calendar API

Google People API

Gmail API

Google Tasks API

Go to APIs & Services > OAuth consent screen.

Choose External user type.

Fill in the required app information (app name, user support email, developer contact).

On the "Scopes" page, you can leave it blank for now.

On the "Test users" page, add the Google account(s) you will be using to test the app.

Go to APIs & Services > Credentials.

Click + CREATE CREDENTIALS -> OAuth client ID.

Select Web application for the Application type.

Under Authorized redirect URIs, click + ADD URI and enter: http://127.0.0.1:5000/oauth2callback

Click Create. A window will pop up. Click DOWNLOAD JSON.

Rename the downloaded file to credentials.json and place it in the root of your project folder.

3. API Keys and Configuration
Clone the Repository:

git clone <your-repo-url>
cd <your-repo-folder>

Get Gemini API Key: Go to Google AI Studio to get your API key.

Get Telegram Bot Token: Talk to the @BotFather on Telegram to create a bot and get its token.

Configure the App: Open config.py and paste in your keys:

# config.py
GEMINI_API_KEY = "YOUR_GEMINI_API_KEY_HERE"
TELEGRAM_BOT_TOKEN = "YOUR_TELEGRAM_BOT_TOKEN_HERE"

4. Install Dependencies
It is highly recommended to use a virtual environment.

python -m venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
pip install -r requirements.txt

Running the Application
You can run the Web UI and the Telegram Bot simultaneously, but they require separate terminals.

To Run the Web UI:
python app.py

Open your browser to http://127.0.0.1:5000.

To Run the Telegram Bot:
python run_telegram.py

Open Telegram and start a chat with the bot you created.

First-Time User Authentication
The first time any user tries to perform an action that requires Google API access (on either platform), the assistant will provide a unique authorization link.

Click the link.

Your browser will open to the Google login and consent screen.

Log in and click "Allow".

You will be redirected to a simple success page. You can now close the browser.

Return to the chat interface (Web or Telegram) and repeat your request. You will now be fully authenticated. This is a one-time process per user.
