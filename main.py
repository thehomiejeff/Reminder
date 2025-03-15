"""
Main entry point for ReminderBot.
Initializes and runs the Telegram bot.
"""
import os
import sys
from src.app import ReminderBotApp
from src.config import BOT_TOKEN
from src.utils.logger import logger

def main():
    """Initialize and run the ReminderBot."""
    try:
        # Create and run the bot
        bot = ReminderBotApp(BOT_TOKEN)
        logger.info("ReminderBot initialized, starting polling...")
        bot.run()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Error running bot: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
