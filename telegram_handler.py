# telegram_handler.py
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
import os
import uuid

class TelegramHandler:
    def __init__(self, token, orchestrator):
        """
        Initializes the Telegram bot handler.
        
        Args:
            token (str): The Telegram Bot API token.
            orchestrator (Orchestrator): The application's main orchestrator instance.
        """
        self.orchestrator = orchestrator
        self.application = ApplicationBuilder().token(token).build()
        
        # Define a temporary folder for image downloads
        self.temp_dir = os.path.join(os.getcwd(), 'telegram_temp')
        if not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir)

        # Register command and message handlers
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_text))
        self.application.add_handler(MessageHandler(filters.PHOTO, self.handle_photo))

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Sends a welcome message when the /start command is issued."""
        await update.message.reply_text('Hello! I am your AI assistant. How can I help you manage your day?')

    async def handle_text(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles regular text messages."""
        user_id = str(update.message.chat_id)
        user_text = update.message.text
        
        print(f"Received text from Telegram user {user_id}: {user_text}")

        message_to_orchestrator = {
            'user_id': user_id,
            'text': user_text
        }
        
        # Send a "typing..." indicator
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        
        response_text = self.orchestrator.handle_message(message_to_orchestrator)
        await update.message.reply_text(response_text)

    async def handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handles photo uploads."""
        user_id = str(update.message.chat_id)
        user_text = update.message.caption or "" # Use caption as text if available
        
        print(f"Received photo from Telegram user {user_id}")
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='upload_photo')
        await update.message.reply_text("Processing your timetable, one moment...")

        temp_path = None
        try:
            # Get the largest available photo
            photo_file = await update.message.photo[-1].get_file()
            
            # Create a unique temporary file path
            file_extension = os.path.splitext(photo_file.file_path)[1]
            temp_path = os.path.join(self.temp_dir, f"{uuid.uuid4()}{file_extension}")
            
            # Download the file
            await photo_file.download_to_drive(temp_path)

            message_to_orchestrator = {
                'user_id': user_id,
                'text': user_text,
                'image_path': temp_path,
                'image_mime_type': 'image/jpeg' # Telegram photos are typically jpeg
            }
            
            response_text = self.orchestrator.handle_message(message_to_orchestrator)
            await update.message.reply_text(response_text)

        except Exception as e:
            print(f"Error handling photo: {e}")
            await update.message.reply_text("Sorry, I had trouble processing that image.")
        finally:
            # The orchestrator handles its own file cleanup now, so we don't delete here.
            pass

    def run(self):
        """Starts the bot."""
        print("Telegram bot is running...")
        self.application.run_polling()
