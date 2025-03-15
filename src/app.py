"""
Main entry point for ReminderBot application.
This module integrates all components and provides a unified interface.
"""
from src.models.database import Database
from src.handlers.command_handlers import CommandHandlers
from src.handlers.callback_handlers import CallbackHandlers
from src.handlers.conversation_handlers import ConversationHandlers
from src.utils.logger import logger
from src.utils.notifications import NotificationManager
from src.utils.scheduler import ReminderScheduler
from src.utils.persistence import DataPersistenceManager

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
)
import asyncio

class ReminderBotApp:
    """Main application class for ReminderBot."""
    
    def __init__(self, token):
        """
        Initialize the ReminderBot application.
        
        Args:
            token (str): Telegram bot token
        """
        self.token = token
        self.db = Database()
        
        # Initialize scheduler
        self.scheduler = ReminderScheduler(self.db)
        
        # Initialize persistence manager
        self.persistence_manager = DataPersistenceManager(self.db)
        
        # Initialize handlers
        self.command_handlers = CommandHandlers(self.db)
        self.callback_handlers = CallbackHandlers(self.db)
        self.conversation_handlers = ConversationHandlers(
            self.db, 
            self.command_handlers, 
            self.callback_handlers
        )
        
        # Create application
        self.application = Application.builder().token(self.token).build()
        
        # Initialize notification manager
        self.notification_manager = None
        
        # Register handlers
        self._register_handlers()
        
        logger.info("ReminderBot application initialized successfully")
    
    def _register_handlers(self):
        """Register all handlers with the application."""
        # Add conversation handlers
        self.application.add_handler(self.conversation_handlers.get_add_reminder_handler())
        self.application.add_handler(self.conversation_handlers.get_settings_handler())
        
        # Add command handlers
        self.application.add_handler(CommandHandler("start", self.command_handlers.start_command))
        self.application.add_handler(CommandHandler("help", self.command_handlers.help_command))
        self.application.add_handler(CommandHandler("list_reminders", self.command_handlers.list_reminders_command))
        self.application.add_handler(CommandHandler("delete_reminder", self.command_handlers.delete_reminder_command))
        self.application.add_handler(CommandHandler("flashlist", self.command_handlers.flashlist_command))
        
        # Add callback query handler for all other callbacks
        self.application.add_handler(CallbackQueryHandler(self.callback_handlers.handle_callback))
        
        # Add error handler
        self.application.add_error_handler(self.error_handler)
        
        # Set up post-startup actions
        self.application.post_init = self.post_init
        self.application.post_shutdown = self.post_shutdown
        
        logger.info("All handlers registered successfully")
    
    async def post_init(self, application):
        """
        Initialize components after application startup.
        
        Args:
            application: Application instance
        """
        # Initialize notification manager
        self.notification_manager = NotificationManager(application.bot, self.db)
        
        # Start notification manager in background
        asyncio.create_task(self.notification_manager.start())
        logger.info("Notification manager started")
    
    async def post_shutdown(self, application):
        """
        Clean up after application shutdown.
        
        Args:
            application: Application instance
        """
        # Stop notification manager
        if self.notification_manager:
            await self.notification_manager.stop()
            logger.info("Notification manager stopped")
    
    async def error_handler(self, update, context):
        """Handle errors in the bot."""
        logger.error(f"Update {update} caused error: {context.error}")
        
        # Send error message to user if possible
        if update and update.effective_message:
            await update.effective_message.reply_text(
                "Sorry, an error occurred. Please try again later."
            )
    
    def run(self):
        """Run the bot."""
        logger.info("Starting ReminderBot...")
        self.application.run_polling()
        
        # Close database connection when bot stops
        self.db.close()
        logger.info("ReminderBot stopped")
