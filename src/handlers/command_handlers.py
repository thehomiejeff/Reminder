"""
Command handlers for ReminderBot.
Defines handlers for bot commands.
"""
from telegram import Update
from telegram.ext import ContextTypes

from src.utils.keyboards import get_main_menu_keyboard
from src.models.database import Database
from src.models.reminder import Reminder
from src.utils.logger import logger

class CommandHandlers:
    """Command handlers for ReminderBot."""
    
    def __init__(self, db: Database):
        """
        Initialize command handlers.
        
        Args:
            db (Database): Database instance
        """
        self.db = db
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /start command.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
        """
        user = update.effective_user
        
        # Add user to database
        self.db.add_user(
            user.id,
            user.first_name,
            user.last_name,
            user.username
        )
        
        # Send welcome message
        welcome_text = (
            f"👋 Hello, {user.first_name}!\n\n"
            f"Welcome to ReminderBot - your structured reminder and productivity assistant.\n\n"
            f"Use the buttons below to navigate or try these commands:\n"
            f"/add_reminder - Add a new reminder\n"
            f"/list_reminders - View all your reminders\n"
            f"/flashlist - Quick view of active tasks\n"
            f"/help - Show help information"
        )
        
        await update.message.reply_text(
            welcome_text,
            reply_markup=get_main_menu_keyboard()
        )
        logger.info(f"User {user.id} ({user.first_name}) started the bot")
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /help command.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
        """
        from src.config import COMMANDS
        
        help_text = (
            "🤖 *ReminderBot Help*\n\n"
            "*Commands:*\n"
        )
        
        # Add all commands to help text
        for command, description in COMMANDS.items():
            help_text += f"/{command} - {description}\n"
        
        help_text += (
            "\n*Using the Bot:*\n"
            "• Use the inline buttons for easy navigation\n"
            "• Add reminders with categories and priorities\n"
            "• Set up recurring tasks for regular reminders\n"
            "• Use /flashlist for a quick overview of your tasks\n"
            "\n*Need more help?*\n"
            "Contact the developer or check the documentation."
        )
        
        await update.message.reply_text(
            help_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        logger.info(f"User {update.effective_user.id} requested help")
    
    async def add_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /add_reminder command.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
            
        Returns:
            int: Next conversation state
        """
        await update.message.reply_text(
            "Let's add a new reminder! 📝\n\n"
            "First, please enter a title for your reminder:"
        )
        logger.info(f"User {update.effective_user.id} started add_reminder process")
        
        # Return the next state (defined in the conversation handler)
        return 1  # ADD_TITLE state
    
    async def list_reminders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /list_reminders command.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
        """
        user_id = update.effective_user.id
        
        # Get reminders from database
        reminders_data = self.db.get_reminders(user_id)
        
        if not reminders_data:
            await update.message.reply_text(
                "You don't have any active reminders.",
                reply_markup=get_main_menu_keyboard()
            )
            logger.info(f"User {user_id} listed reminders (none found)")
            return
        
        # Convert to Reminder objects
        reminders = [Reminder.from_dict(r) for r in reminders_data]
        
        # Format reminders list
        reminders_text = "📋 *Your Reminders*\n\n"
        
        for i, reminder in enumerate(reminders, 1):
            due_date = reminder.get_formatted_due_date() if reminder.due_date else "No due date"
            priority_emoji = reminder.get_priority_emoji()
            recurring = "🔄 " if reminder.is_recurring else ""
            
            reminders_text += (
                f"{i}. {priority_emoji} *{reminder.title}*\n"
                f"   {recurring}Due: {due_date}\n"
                f"   Category: {reminder.category}\n\n"
            )
        
        # Create keyboard for reminder actions
        from src.utils.keyboards import get_reminders_list_keyboard
        
        await update.message.reply_text(
            reminders_text,
            parse_mode='Markdown',
            reply_markup=get_reminders_list_keyboard(reminders)
        )
        logger.info(f"User {user_id} listed {len(reminders)} reminders")
    
    async def delete_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /delete_reminder command.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
        """
        user_id = update.effective_user.id
        
        # Get reminders from database
        reminders_data = self.db.get_reminders(user_id)
        
        if not reminders_data:
            await update.message.reply_text(
                "You don't have any active reminders to delete.",
                reply_markup=get_main_menu_keyboard()
            )
            logger.info(f"User {user_id} attempted to delete reminders (none found)")
            return
        
        # Convert to Reminder objects
        reminders = [Reminder.from_dict(r) for r in reminders_data]
        
        # Create keyboard for reminder selection
        from src.utils.keyboards import get_reminders_list_keyboard
        
        await update.message.reply_text(
            "Select a reminder to delete:",
            reply_markup=get_reminders_list_keyboard(reminders)
        )
        logger.info(f"User {user_id} requested to delete a reminder")
    
    async def flashlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /flashlist command for quick task overview.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
        """
        user_id = update.effective_user.id
        
        # Get reminders from database
        reminders_data = self.db.get_reminders(user_id)
        
        if not reminders_data:
            await update.message.reply_text(
                "⚡ *Flash List*\n\n"
                "You don't have any active reminders.",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
            logger.info(f"User {user_id} requested flashlist (none found)")
            return
        
        # Convert to Reminder objects
        reminders = [Reminder.from_dict(r) for r in reminders_data]
        
        # Sort reminders: due first, then by priority
        def sort_key(reminder):
            # Priority values for sorting (higher number = higher priority)
            priority_values = {'high': 3, 'medium': 2, 'low': 1}
            
            # If due date exists, use it as primary sort key
            if reminder.due_date:
                return (0, reminder.due_date, -priority_values.get(reminder.priority, 0))
            # If no due date, sort by priority, then title
            return (1, -priority_values.get(reminder.priority, 0), reminder.title)
        
        sorted_reminders = sorted(reminders, key=sort_key)
        
        # Format flash list
        flash_text = "⚡ *Flash List*\n\n"
        
        for reminder in sorted_reminders:
            due_date = reminder.get_formatted_due_date('%b %d, %H:%M') if reminder.due_date else "No due date"
            priority_emoji = reminder.get_priority_emoji()
            recurring = "🔄 " if reminder.is_recurring else ""
            
            flash_text += f"{priority_emoji} {recurring}*{reminder.title}* - {due_date}\n"
        
        await update.message.reply_text(
            flash_text,
            parse_mode='Markdown',
            reply_markup=get_main_menu_keyboard()
        )
        logger.info(f"User {user_id} requested flashlist with {len(reminders)} reminders")
    
    async def cancel_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /cancel command to cancel current operation.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
            
        Returns:
            int: ConversationHandler.END to end the conversation
        """
        from telegram.ext import ConversationHandler
        
        await update.message.reply_text(
            "Operation cancelled. What would you like to do next?",
            reply_markup=get_main_menu_keyboard()
        )
        
        # Clear user data
        context.user_data.clear()
        logger.info(f"User {update.effective_user.id} cancelled current operation")
        
        return ConversationHandler.END
