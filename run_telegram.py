# run_telegram.py
from orchestrator import Orchestrator
from telegram_handler import TelegramHandler
import config

if __name__ == '__main__':
    if not config.TELEGRAM_BOT_TOKEN or config.TELEGRAM_BOT_TOKEN == "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        print("FATAL: Telegram Bot Token is not configured in config.py")
    else:
        # Initialize the single Orchestrator instance
        orchestrator = Orchestrator()
        
        # Initialize the Telegram Handler with the orchestrator
        telegram_bot = TelegramHandler(token=config.TELEGRAM_BOT_TOKEN, orchestrator=orchestrator)
        
        # Start the bot
        telegram_bot.run()
