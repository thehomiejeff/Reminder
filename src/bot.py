"""
Main bot script for ReminderBot.
Initializes and runs the Telegram bot.
"""
import os
import logging
from datetime import datetime, timedelta
import pytz
from telegram import Update, Bot
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ConversationHandler,
    filters,
    ContextTypes
)

# Import configuration and utilities
from src.config import BOT_TOKEN, COMMANDS, DEFAULT_TIMEZONE
from src.utils.logger import logger
from src.utils.keyboards import get_main_menu_keyboard
from src.models.database import Database
from src.models.reminder import Reminder

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

class ReminderBot:
    """Main ReminderBot class."""
    
    def __init__(self):
        """Initialize the bot with necessary components."""
        # Initialize database
        self.db = Database()
        
        # Create application
        self.application = Application.builder().token(BOT_TOKEN).build()
        
        # Register handlers
        self._register_handlers()
        
        logger.info("ReminderBot initialized successfully")
    
    def _register_handlers(self):
        """Register all command and callback handlers."""
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.start_command))
        self.application.add_handler(CommandHandler("help", self.help_command))
        self.application.add_handler(CommandHandler("add_reminder", self.add_reminder_command))
        self.application.add_handler(CommandHandler("list_reminders", self.list_reminders_command))
        self.application.add_handler(CommandHandler("delete_reminder", self.delete_reminder_command))
        self.application.add_handler(CommandHandler("flashlist", self.flashlist_command))
        
        # Callback query handler
        self.application.add_handler(CallbackQueryHandler(self.handle_callback))
        
        # Add conversation handler for adding reminders
        add_reminder_conv = ConversationHandler(
            entry_points=[CommandHandler("add_reminder", self.add_reminder_command)],
            states={
                ADD_TITLE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_title)],
                ADD_DESCRIPTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_description)],
                ADD_DUE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_due_date)],
                ADD_CATEGORY: [CallbackQueryHandler(self.process_category, pattern=r"^category_")],
                ADD_PRIORITY: [CallbackQueryHandler(self.process_priority, pattern=r"^priority_")],
                ADD_RECURRING: [CallbackQueryHandler(self.process_recurring_choice, pattern=r"^recurring_")],
                RECURRING_SETUP: [MessageHandler(filters.TEXT & ~filters.COMMAND, self.process_recurring_setup)],
            },
            fallbacks=[CommandHandler("cancel", self.cancel_conversation)],
            name="add_reminder_conversation",
            persistent=False,
        )
        self.application.add_handler(add_reminder_conv)
        
        # Error handler
        self.application.add_error_handler(self.error_handler)
        
        logger.info("All handlers registered successfully")
    
    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /start command."""
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
    
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /help command."""
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
    
    async def add_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /add_reminder command."""
        await update.message.reply_text(
            "Let's add a new reminder! 📝\n\n"
            "First, please enter a title for your reminder:"
        )
        return ADD_TITLE
    
    async def process_title(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process the reminder title input."""
        title = update.message.text
        
        # Store title in user data
        context.user_data['reminder_title'] = title
        
        await update.message.reply_text(
            f"Title: *{title}*\n\n"
            f"Now, please enter a description (or send 'skip' to skip):",
            parse_mode='Markdown'
        )
        return ADD_DESCRIPTION
    
    async def process_description(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process the reminder description input."""
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
        return ADD_DUE_DATE
    
    async def process_due_date(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process the reminder due date input."""
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
        from src.utils.keyboards import get_categories_keyboard
        await update.message.reply_text(
            f"Due date: *{due_date_display}*\n\n"
            f"Please select a category for your reminder:",
            parse_mode='Markdown',
            reply_markup=get_categories_keyboard()
        )
        return ADD_CATEGORY
    
    async def process_category(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process the reminder category selection."""
        query = update.callback_query
        await query.answer()
        
        # Extract category from callback data
        category = query.data.replace('category_', '')
        
        # Store category in user data
        context.user_data['reminder_category'] = category
        
        # Ask for priority
        from src.utils.keyboards import get_priority_keyboard
        await query.edit_message_text(
            f"Category: *{category}*\n\n"
            f"Please select a priority level:",
            parse_mode='Markdown',
            reply_markup=get_priority_keyboard()
        )
        return ADD_PRIORITY
    
    async def process_priority(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process the reminder priority selection."""
        query = update.callback_query
        await query.answer()
        
        # Extract priority from callback data
        priority = query.data.replace('priority_', '')
        
        # Store priority in user data
        context.user_data['reminder_priority'] = priority
        
        # Ask if recurring
        from src.utils.keyboards import get_yes_no_keyboard
        await query.edit_message_text(
            f"Priority: *{priority.capitalize()}*\n\n"
            f"Is this a recurring reminder?",
            parse_mode='Markdown',
            reply_markup=get_yes_no_keyboard('recurring')
        )
        return ADD_RECURRING
    
    async def process_recurring_choice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process the recurring reminder choice."""
        query = update.callback_query
        await query.answer()
        
        # Check if user wants a recurring reminder
        is_recurring = query.data == 'recurring_yes'
        
        if is_recurring:
            # Ask for recurring pattern
            from src.utils.keyboards import get_recurring_options_keyboard
            await query.edit_message_text(
                "Please select a recurrence pattern:",
                reply_markup=get_recurring_options_keyboard()
            )
            return RECURRING_SETUP
        else:
            # Not recurring, save the reminder
            return await self.save_reminder(update, context)
    
    async def process_recurring_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process the recurring reminder setup."""
        # This would handle custom recurrence patterns
        # For simplicity, we'll just save the reminder with basic recurrence
        return await self.save_reminder(update, context)
    
    async def save_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Save the reminder to the database."""
        query = update.callback_query
        
        # Get user data
        user_id = query.from_user.id
        title = context.user_data.get('reminder_title')
        description = context.user_data.get('reminder_description')
        due_date = context.user_data.get('reminder_due_date')
        category = context.user_data.get('reminder_category')
        priority = context.user_data.get('reminder_priority')
        
        # Determine if recurring based on callback data
        is_recurring = False
        recurrence_pattern = None
        
        if query.data.startswith('recurring_'):
            recurrence_type = query.data.replace('recurring_', '')
            if recurrence_type != 'no':
                is_recurring = True
                recurrence_pattern = {'type': recurrence_type}
        
        # Create reminder in database
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
            await query.edit_message_text(
                f"✅ Reminder created successfully!\n\n"
                f"*{title}*\n"
                f"Category: {category}\n"
                f"Priority: {priority.capitalize()}\n"
                f"Due: {due_date.strftime('%Y-%m-%d %H:%M') if due_date else 'Not set'}\n"
                f"Recurring: {'Yes' if is_recurring else 'No'}",
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
        else:
            # Error message
            await query.edit_message_text(
                "❌ Failed to create reminder. Please try again.",
                reply_markup=get_main_menu_keyboard()
            )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    async def cancel_conversation(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Cancel the current conversation."""
        await update.message.reply_text(
            "Operation cancelled. What would you like to do next?",
            reply_markup=get_main_menu_keyboard()
        )
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
    
    async def list_reminders_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /list_reminders command."""
        user_id = update.effective_user.id
        
        # Get reminders from database
        reminders_data = self.db.get_reminders(user_id)
        
        if not reminders_data:
            await update.message.reply_text(
                "You don't have any active reminders.",
                reply_markup=get_main_menu_keyboard()
            )
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
    
    async def delete_reminder_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /delete_reminder command."""
        user_id = update.effective_user.id
        
        # Get reminders from database
        reminders_data = self.db.get_reminders(user_id)
        
        if not reminders_data:
            await update.message.reply_text(
                "You don't have any active reminders to delete.",
                reply_markup=get_main_menu_keyboard()
            )
            return
        
        # Convert to Reminder objects
        reminders = [Reminder.from_dict(r) for r in reminders_data]
        
        # Create keyboard for reminder selection
        from src.utils.keyboards import get_reminders_list_keyboard
        
        await update.message.reply_text(
            "Select a reminder to delete:",
            reply_markup=get_reminders_list_keyboard(reminders)
        )
    
    async def flashlist_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle the /flashlist command for quick task overview."""
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
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards."""
        query = update.callback_query
        await query.answer()
        
        # Extract callback data
        callback_data = query.data
        
        # Handle different callback types
        if callback_data == "add_reminder":
            # Redirect to add reminder command
            await query.edit_message_text(
                "Let's add a new reminder! 📝\n\n"
                "Please enter a title for your reminder:"
            )
            return ADD_TITLE
            
        elif callback_data == "list_reminders":
            # Get reminders and display them
            user_id = query.from_user.id
            reminders_data = self.db.get_reminders(user_id)
            
            if not reminders_data:
                await query.edit_message_text(
                    "You don't have any active reminders.",
                    reply_markup=get_main_menu_keyboard()
                )
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
            
            await query.edit_message_text(
                reminders_text,
                parse_mode='Markdown',
                reply_markup=get_reminders_list_keyboard(reminders)
            )
            
        elif callback_data == "delete_reminder":
            # Show reminders for deletion
            user_id = query.from_user.id
            reminders_data = self.db.get_reminders(user_id)
            
            if not reminders_data:
                await query.edit_message_text(
                    "You don't have any active reminders to delete.",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Convert to Reminder objects
            reminders = [Reminder.from_dict(r) for r in reminders_data]
            
            # Create keyboard for reminder selection
            from src.utils.keyboards import get_reminders_list_keyboard
            
            await query.edit_message_text(
                "Select a reminder to delete:",
                reply_markup=get_reminders_list_keyboard(reminders)
            )
            
        elif callback_data == "flashlist":
            # Show quick overview of tasks
            user_id = query.from_user.id
            reminders_data = self.db.get_reminders(user_id)
            
            if not reminders_data:
                await query.edit_message_text(
                    "⚡ *Flash List*\n\n"
                    "You don't have any active reminders.",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard()
                )
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
            
            await query.edit_message_text(
                flash_text,
                parse_mode='Markdown',
                reply_markup=get_main_menu_keyboard()
            )
            
        elif callback_data == "recurring_tasks":
            # Show recurring tasks
            user_id = query.from_user.id
            reminders_data = self.db.get_reminders(user_id)
            
            # Filter for recurring reminders
            recurring_reminders_data = [r for r in reminders_data if r.get('is_recurring')]
            
            if not recurring_reminders_data:
                await query.edit_message_text(
                    "🔄 *Recurring Tasks*\n\n"
                    "You don't have any recurring reminders.",
                    parse_mode='Markdown',
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Convert to Reminder objects
            reminders = [Reminder.from_dict(r) for r in recurring_reminders_data]
            
            # Format recurring reminders list
            reminders_text = "🔄 *Recurring Tasks*\n\n"
            
            for i, reminder in enumerate(reminders, 1):
                due_date = reminder.get_formatted_due_date() if reminder.due_date else "No due date"
                priority_emoji = reminder.get_priority_emoji()
                recurrence_text = reminder.get_recurrence_text()
                
                reminders_text += (
                    f"{i}. {priority_emoji} *{reminder.title}*\n"
                    f"   Pattern: {recurrence_text}\n"
                    f"   Next: {due_date}\n"
                    f"   Category: {reminder.category}\n\n"
                )
            
            # Create keyboard for reminder actions
            from src.utils.keyboards import get_reminders_list_keyboard
            
            await query.edit_message_text(
                reminders_text,
                parse_mode='Markdown',
                reply_markup=get_reminders_list_keyboard(reminders)
            )
            
        elif callback_data == "settings":
            # Show settings menu
            from src.utils.keyboards import get_settings_keyboard
            
            await query.edit_message_text(
                "⚙️ *Settings*\n\n"
                "Configure your ReminderBot preferences:",
                parse_mode='Markdown',
                reply_markup=get_settings_keyboard()
            )
            
        elif callback_data == "back_to_main":
            # Return to main menu
            await query.edit_message_text(
                "What would you like to do?",
                reply_markup=get_main_menu_keyboard()
            )
            
        elif callback_data.startswith("reminder_"):
            # Show reminder details and actions
            reminder_id = int(callback_data.replace("reminder_", ""))
            reminder_data = self.db.get_reminder(reminder_id)
            
            if not reminder_data:
                await query.edit_message_text(
                    "Reminder not found. It may have been deleted.",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Convert to Reminder object
            reminder = Reminder.from_dict(reminder_data)
            
            # Format reminder details
            details_text = (
                f"📌 *{reminder.title}*\n\n"
                f"Description: {reminder.description or 'None'}\n"
                f"Due: {reminder.get_formatted_due_date() if reminder.due_date else 'Not set'}\n"
                f"Category: {reminder.category}\n"
                f"Priority: {reminder.priority.capitalize()}\n"
            )
            
            if reminder.is_recurring:
                details_text += f"Recurring: {reminder.get_recurrence_text()}\n"
            
            # Create keyboard for reminder actions
            from src.utils.keyboards import get_reminder_actions_keyboard
            
            await query.edit_message_text(
                details_text,
                parse_mode='Markdown',
                reply_markup=get_reminder_actions_keyboard(reminder_id)
            )
            
        elif callback_data.startswith("complete_"):
            # Mark reminder as completed
            reminder_id = int(callback_data.replace("complete_", ""))
            success = self.db.mark_reminder_completed(reminder_id)
            
            if success:
                await query.edit_message_text(
                    "✅ Reminder marked as completed!",
                    reply_markup=get_main_menu_keyboard()
                )
            else:
                await query.edit_message_text(
                    "❌ Failed to update reminder. Please try again.",
                    reply_markup=get_main_menu_keyboard()
                )
                
        elif callback_data.startswith("confirm_delete_"):
            # Confirm deletion of reminder
            reminder_id = int(callback_data.replace("confirm_delete_", ""))
            reminder_data = self.db.get_reminder(reminder_id)
            
            if not reminder_data:
                await query.edit_message_text(
                    "Reminder not found. It may have been deleted already.",
                    reply_markup=get_main_menu_keyboard()
                )
                return
            
            # Create confirmation keyboard
            from src.utils.keyboards import get_yes_no_keyboard
            
            await query.edit_message_text(
                f"Are you sure you want to delete this reminder?\n\n"
                f"*{reminder_data['title']}*",
                parse_mode='Markdown',
                reply_markup=get_yes_no_keyboard(f"delete_{reminder_id}")
            )
            
        elif callback_data.startswith("delete_"):
            # Process deletion confirmation
            parts = callback_data.split('_')
            reminder_id = int(parts[1])
            confirmed = parts[2] == 'yes'
            
            if confirmed:
                success = self.db.delete_reminder(reminder_id)
                
                if success:
                    await query.edit_message_text(
                        "✅ Reminder deleted successfully!",
                        reply_markup=get_main_menu_keyboard()
                    )
                else:
                    await query.edit_message_text(
                        "❌ Failed to delete reminder. Please try again.",
                        reply_markup=get_main_menu_keyboard()
                    )
            else:
                # User cancelled deletion
                await query.edit_message_text(
                    "Deletion cancelled.",
                    reply_markup=get_main_menu_keyboard()
                )
                
        elif callback_data.startswith("postpone_"):
            # Handle postpone action
            parts = callback_data.split('_')
            reminder_id = int(parts[1])
            
            if len(parts) == 2:
                # Show postpone options
                from src.utils.keyboards import get_postpone_options_keyboard
                
                await query.edit_message_text(
                    "How long would you like to postpone this reminder?",
                    reply_markup=get_postpone_options_keyboard(reminder_id)
                )
            else:
                # Process postpone duration
                duration = parts[2]
                reminder_data = self.db.get_reminder(reminder_id)
                
                if not reminder_data:
                    await query.edit_message_text(
                        "Reminder not found. It may have been deleted.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    return
                
                # Calculate new due date
                current_due_date = None
                if reminder_data['due_date']:
                    if isinstance(reminder_data['due_date'], str):
                        current_due_date = datetime.fromisoformat(reminder_data['due_date'].replace('Z', '+00:00'))
                    else:
                        current_due_date = reminder_data['due_date']
                
                if not current_due_date:
                    current_due_date = datetime.now()
                
                # Apply postpone duration
                if duration == '1h':
                    new_due_date = current_due_date + timedelta(hours=1)
                elif duration == '3h':
                    new_due_date = current_due_date + timedelta(hours=3)
                elif duration == '1d':
                    new_due_date = current_due_date + timedelta(days=1)
                elif duration == '1w':
                    new_due_date = current_due_date + timedelta(weeks=1)
                else:
                    new_due_date = current_due_date
                
                # Update reminder
                success = self.db.update_reminder(reminder_id, due_date=new_due_date)
                
                if success:
                    await query.edit_message_text(
                        f"✅ Reminder postponed successfully!\n\n"
                        f"New due date: {new_due_date.strftime('%Y-%m-%d %H:%M')}",
                        reply_markup=get_main_menu_keyboard()
                    )
                else:
                    await query.edit_message_text(
                        "❌ Failed to postpone reminder. Please try again.",
                        reply_markup=get_main_menu_keyboard()
                    )
    
    async def error_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
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


if __name__ == "__main__":
    # Create and run the bot
    bot = ReminderBot()
    bot.run()
