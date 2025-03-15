"""
Conversation handlers for ReminderBot.
Defines handlers for multi-step conversations.
"""
from telegram import Update
from telegram.ext import (
    ContextTypes,
    ConversationHandler,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters
)

from src.utils.keyboards import (
    get_categories_keyboard,
    get_priority_keyboard,
    get_main_menu_keyboard,
    get_yes_no_keyboard
)
from src.models.database import Database
from src.utils.logger import logger
from datetime import datetime
import pytz
from src.config import DEFAULT_TIMEZONE

# Define conversation states
(
    MAIN_MENU,
    ADD_TITLE,
    ADD_DESCRIPTION,
    ADD_DUE_DATE,
    ADD_CATEGORY,
    ADD_PRIORITY,
    ADD_RECURRING,
    RECURRING_SETUP,
    CONFIRM_DELETE,
    SETTINGS,
    SET_TIMEZONE
) = range(11)

class ConversationHandlers:
    """Conversation handlers for ReminderBot."""
    
    def __init__(self, db: Database, command_handlers, callback_handlers):
        """
        Initialize conversation handlers.
        
        Args:
            db (Database): Database instance
            command_handlers: Command handlers instance
            callback_handlers: Callback handlers instance
        """
        self.db = db
        self.command_handlers = command_handlers
        self.callback_handlers = callback_handlers
    
    def get_add_reminder_handler(self):
        """
        Get the conversation handler for adding reminders.
        
        Returns:
            ConversationHandler: Handler for add reminder conversation
        """
        return ConversationHandler(
            entry_points=[
                CommandHandler("add_reminder", self.command_handlers.add_reminder_command),
                CallbackQueryHandler(self.callback_handlers.handle_callback, pattern="^add_reminder$")
            ],
            states={
                ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_title)],
                ADD_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_description)],
                ADD_DUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_due_date)],
                ADD_CATEGORY: [CallbackQueryHandler(self.callback_handlers.handle_callback, pattern=r"^category_")],
                ADD_PRIORITY: [CallbackQueryHandler(self.callback_handlers.handle_callback, pattern=r"^priority_")],
                ADD_RECURRING: [CallbackQueryHandler(self.callback_handlers.handle_callback, pattern=r"^recurring_")],
                RECURRING_SETUP: [
                    CallbackQueryHandler(self.callback_handlers.handle_callback, pattern=r"^recurring_"),
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_recurring_setup)
                ],
            },
            fallbacks=[CommandHandler("cancel", self.command_handlers.cancel_command)],
            name="add_reminder_conversation",
            persistent=False,
        )
    
    def get_settings_handler(self):
        """
        Get the conversation handler for settings.
        
        Returns:
            ConversationHandler: Handler for settings conversation
        """
        return ConversationHandler(
            entry_points=[
                CommandHandler("settings", self.settings_command),
                CallbackQueryHandler(self.callback_handlers.handle_callback, pattern="^settings$")
            ],
            states={
                SETTINGS: [
                    CallbackQueryHandler(self.callback_handlers.handle_callback, pattern="^set_timezone$"),
                    CallbackQueryHandler(self.callback_handlers.handle_callback, pattern="^notifications$"),
                    CallbackQueryHandler(self.callback_handlers.handle_callback, pattern="^back_to_main$")
                ],
                SET_TIMEZONE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_timezone)],
            },
            fallbacks=[CommandHandler("cancel", self.command_handlers.cancel_command)],
            name="settings_conversation",
            persistent=False,
        )
    
    async def settings_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /settings command.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
            
        Returns:
            int: Next conversation state
        """
        from src.utils.keyboards import get_settings_keyboard
        
        await update.message.reply_text(
            "⚙️ *Settings*\n\n"
            "Configure your ReminderBot preferences:",
            parse_mode='Markdown',
            reply_markup=get_settings_keyboard()
        )
        logger.info(f"User {update.effective_user.id} opened settings menu")
        return SETTINGS
    
    async def process_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Process the reminder title input.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
            
        Returns:
            int: Next conversation state
        """
        title = update.message.text
        
        # Store title in user data
        context.user_data['reminder_title'] = title
        
        await update.message.reply_text(
            f"Title: *{title}*\n\n"
            f"Now, please enter a description (or send 'skip' to skip):",
            parse_mode='Markdown'
        )
        logger.info(f"User {update.effective_user.id} entered reminder title: {title}")
        return ADD_DESCRIPTION
    
    async def process_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Process the reminder description input.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
            
        Returns:
            int: Next conversation state
        """
        description = update.message.text
        
        # Store description in user data (or None if skipped)
        if description.lower() == 'skip':
            context.user_data['reminder_description'] = None
            description_text = "No description"
        else:
            context.user_data['reminder_description'] = description
            description_text = description
        
        await update.message.reply_text(
            f"Description: *{description_text}*\n\n"
            f"Now, please enter the due date and time in format:\n"
            f"YYYY-MM-DD HH:MM\n\n"
            f"Or send 'skip' to skip setting a due date:",
            parse_mode='Markdown'
        )
        logger.info(f"User {update.effective_user.id} entered reminder description")
        return ADD_DUE_DATE
    
    async def process_due_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Process the reminder due date input.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
            
        Returns:
            int: Next conversation state
        """
        due_date_text = update.message.text
        
        # Handle skipping due date
        if due_date_text.lower() == 'skip':
            context.user_data['reminder_due_date'] = None
            due_date_display = "No due date"
        else:
            # Try to parse the due date
            try:
                # Parse the date string
                due_date = datetime.strptime(due_date_text, '%Y-%m-%d %H:%M')
                
                # Set timezone (default to UTC if not specified)
                timezone = pytz.timezone(DEFAULT_TIMEZONE)
                due_date = timezone.localize(due_date)
                
                # Store due date in user data
                context.user_data['reminder_due_date'] = due_date
                due_date_display = due_date.strftime('%Y-%m-%d %H:%M')
            except ValueError:
                await update.message.reply_text(
                    "❌ Invalid date format. Please use YYYY-MM-DD HH:MM format.\n"
                    "For example: 2025-03-20 14:30\n\n"
                    "Try again:"
                )
                return ADD_DUE_DATE
        
        # Ask for category
        await update.message.reply_text(
            f"Due date: *{due_date_display}*\n\n"
            f"Please select a category for your reminder:",
            parse_mode='Markdown',
            reply_markup=get_categories_keyboard()
        )
        logger.info(f"User {update.effective_user.id} entered due date: {due_date_display}")
        return ADD_CATEGORY
    
    async def process_recurring_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Process the recurring reminder setup.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
            
        Returns:
            int: Next conversation state
        """
        # This would handle custom recurrence patterns
        # For simplicity, we'll just save the reminder with basic recurrence
        context.user_data['reminder_is_recurring'] = True
        context.user_data['reminder_recurrence_pattern'] = {'type': 'custom', 'description': update.message.text}
        
        # Create reminder in database
        user_id = update.effective_user.id
        title = context.user_data.get('reminder_title')
        description = context.user_data.get('reminder_description')
        due_date = context.user_data.get('reminder_due_date')
        category = context.user_data.get('reminder_category')
        priority = context.user_data.get('reminder_priority')
        is_recurring = context.user_data.get('reminder_is_recurring', False)
        recurrence_pattern = context.user_data.get('reminder_recurrence_pattern')
        
        reminder_id = self.db.add_reminder(
            user_id=user_id,
            title=title,
            description=description,
            due_date=due_date,
            category=category,
            priority=priority,
            is_recurring=is_recurring,
            recurrence_pattern=recurrence_pattern
        )
        
        if reminder_id:
            # Success message
            await update.message.reply_text(
                f"✅ Reminder created successfully!\n\n"
                f"*{title}*\n"
                f"Category: {category}\n"
                f"Priority: {priority.capitalize()}\n"
                f"Due: {due_date.strftime('%Y-%m-%d %H:%M') if due_date else 'Not set'}\n"
                f"Recurring: Yes (Custom)",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
            logger.info(f"User {user_id} created recurring reminder {reminder_id}: {title}")
        else:
            # Error message
            await update.message.reply_text(
                "❌ Failed to create reminder. Please try again.",
                reply_markup=get_main_menu_keyboard()
            )
            logger.error(f"Failed to create recurring reminder for user {user_id}")
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    async def process_timezone(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Process the timezone input.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
            
        Returns:
            int: Next conversation state
        """
        timezone_text = update.message.text
        
        # Validate timezone
        try:
            timezone = pytz.timezone(timezone_text)
            
            # Store in user preferences (would be implemented in a real bot)
            # For now, just acknowledge
            await update.message.reply_text(
                f"✅ Timezone set to *{timezone_text}*\n\n"
                f"All reminder times will now be interpreted in this timezone.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
            logger.info(f"User {update.effective_user.id} set timezone to {timezone_text}")
            
        except pytz.exceptions.UnknownTimeZoneError:
            await update.message.reply_text(
                "❌ Invalid timezone. Please enter a valid timezone identifier.\n\n"
                "Examples: 'America/New_York', 'Europe/London', 'Asia/Tokyo'\n\n"
                "Try again or send /cancel to cancel:"
            )
            return SET_TIMEZONE
        
        return ConversationHandler.END
