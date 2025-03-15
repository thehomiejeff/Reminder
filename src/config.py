"""
Configuration module for ReminderBot.
Loads environment variables and provides configuration settings.
"""
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Bot Configuration
BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
if not BOT_TOKEN:
    raise ValueError("No bot token found. Please set TELEGRAM_BOT_TOKEN in .env file")

# Database Configuration
DATABASE_PATH = os.getenv('DATABASE_PATH', 'data/reminderbot.db')
# Ensure the directory exists
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)

# Logging Configuration
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
LOG_FILE = os.getenv('LOG_FILE', 'logs/reminderbot.log')
# Ensure the log directory exists
os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)

# Convert string log level to logging constant
LOG_LEVEL_MAP = {
    'DEBUG': logging.DEBUG,
    'INFO': logging.INFO,
    'WARNING': logging.WARNING,
    'ERROR': logging.ERROR,
    'CRITICAL': logging.CRITICAL
}
LOGGING_LEVEL = LOG_LEVEL_MAP.get(LOG_LEVEL, logging.INFO)

# Timezone Configuration
DEFAULT_TIMEZONE = os.getenv('DEFAULT_TIMEZONE', 'UTC')

# Bot Command Definitions
COMMANDS = {
    'start': 'Start the bot and get a welcome message',
    'help': 'Show help information',
    'add_reminder': 'Add a new reminder',
    'list_reminders': 'List all active reminders',
    'delete_reminder': 'Delete a specific reminder',
    'flashlist': 'Quick view of all active tasks'
}

# Reminder Categories
REMINDER_CATEGORIES = ['Work', 'Personal', 'Fitness', 'Health', 'Shopping', 'Other']

# Recurring Options
RECURRING_OPTIONS = {
    'daily': 'Every day',
    'weekly': 'Every week',
    'monthly': 'Every month',
    'custom': 'Custom schedule'
}

# Priority Levels
PRIORITY_LEVELS = {
    'high': '⚠️ High',
    'medium': '⚡ Medium',
    'low': '✓ Low'
}
