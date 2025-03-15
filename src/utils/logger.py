"""
Logging configuration module for ReminderBot.
Sets up logging with file and console handlers.
"""
import logging
import os
from logging.handlers import RotatingFileHandler
from src.config import LOGGING_LEVEL, LOG_FILE

def setup_logging():
    """
    Configure logging for the application.
    Sets up both file and console handlers with appropriate formatting.
    """
    # Create logger
    logger = logging.getLogger('reminderbot')
    logger.setLevel(LOGGING_LEVEL)
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Ensure log directory exists
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    
    # Create file handler for logging to a file
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=10485760,  # 10MB
        backupCount=5
    )
    file_handler.setLevel(LOGGING_LEVEL)
    file_handler.setFormatter(formatter)
    
    # Create console handler for logging to console
    console_handler = logging.StreamHandler()
    console_handler.setLevel(LOGGING_LEVEL)
    console_handler.setFormatter(formatter)
    
    # Add handlers to logger
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger

# Create and configure logger
logger = setup_logging()
