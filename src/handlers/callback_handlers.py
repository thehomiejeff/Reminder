"""
Callback handlers for ReminderBot.
Defines handlers for inline keyboard callbacks.
"""
from telegram import Update, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

from src.utils.keyboards import (
    get_main_menu_keyboard,
    get_reminders_list_keyboard,
    get_categories_keyboard,
    get_priority_keyboard,
    get_recurring_options_keyboard,
    get_yes_no_keyboard,
    get_reminder_actions_keyboard,
    get_postpone_options_keyboard,
    get_settings_keyboard
)
from src.models.database import Database
from src.models.reminder import Reminder
from src.utils.logger import logger
from datetime import datetime, timedelta
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

class CallbackHandlers:
    """Callback handlers for ReminderBot."""
    
    def __init__(self, db: Database):
        """
        Initialize callback handlers.
        
        Args:
            db (Database): Database instance
        """
        self.db = db
    
    async def handle_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle callback queries from inline keyboards.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
            
        Returns:
            int: Next conversation state if applicable
        """
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
            logger.info(f"User {query.from_user.id} started add_reminder via callback")
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
                logger.info(f"User {user_id} listed reminders via callback (none found)")
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
            
            await query.edit_message_text(
                reminders_text,
                parse_mode='Markdown',
                reply_markup=get_reminders_list_keyboard(reminders)
            )
            logger.info(f"User {user_id} listed {len(reminders)} reminders via callback")
            
        elif callback_data == "delete_reminder":
            # Show reminders for deletion
            user_id = query.from_user.id
            reminders_data = self.db.get_reminders(user_id)
            
            if not reminders_data:
                await query.edit_message_text(
                    "You don't have any active reminders to delete.",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.info(f"User {user_id} attempted to delete reminders via callback (none found)")
                return
            
            # Convert to Reminder objects
            reminders = [Reminder.from_dict(r) for r in reminders_data]
            
            await query.edit_message_text(
                "Select a reminder to delete:",
                reply_markup=get_reminders_list_keyboard(reminders)
            )
            logger.info(f"User {user_id} requested to delete a reminder via callback")
            
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
                logger.info(f"User {user_id} requested flashlist via callback (none found)")
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
            logger.info(f"User {user_id} requested flashlist via callback with {len(reminders)} reminders")
            
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
                logger.info(f"User {user_id} requested recurring tasks via callback (none found)")
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
            
            await query.edit_message_text(
                reminders_text,
                parse_mode='Markdown',
                reply_markup=get_reminders_list_keyboard(reminders)
            )
            logger.info(f"User {user_id} requested recurring tasks via callback with {len(reminders)} reminders")
            
        elif callback_data == "settings":
            # Show settings menu
            await query.edit_message_text(
                "⚙️ *Settings*\n\n"
                "Configure your ReminderBot preferences:",
                parse_mode='Markdown',
                reply_markup=get_settings_keyboard()
            )
            logger.info(f"User {query.from_user.id} opened settings menu")
            
        elif callback_data == "back_to_main":
            # Return to main menu
            await query.edit_message_text(
                "What would you like to do?",
                reply_markup=get_main_menu_keyboard()
            )
            logger.info(f"User {query.from_user.id} returned to main menu")
            
        elif callback_data.startswith("reminder_"):
            # Show reminder details and actions
            reminder_id = int(callback_data.replace("reminder_", ""))
            reminder_data = self.db.get_reminder(reminder_id)
            
            if not reminder_data:
                await query.edit_message_text(
                    "Reminder not found. It may have been deleted.",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.warning(f"User {query.from_user.id} tried to access non-existent reminder {reminder_id}")
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
            
            await query.edit_message_text(
                details_text,
                parse_mode='Markdown',
                reply_markup=get_reminder_actions_keyboard(reminder_id)
            )
            logger.info(f"User {query.from_user.id} viewed details for reminder {reminder_id}")
            
        elif callback_data.startswith("complete_"):
            # Mark reminder as completed
            reminder_id = int(callback_data.replace("complete_", ""))
            success = self.db.mark_reminder_completed(reminder_id)
            
            if success:
                await query.edit_message_text(
                    "✅ Reminder marked as completed!",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.info(f"User {query.from_user.id} marked reminder {reminder_id} as completed")
            else:
                await query.edit_message_text(
                    "❌ Failed to update reminder. Please try again.",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.error(f"Failed to mark reminder {reminder_id} as completed for user {query.from_user.id}")
                
        elif callback_data.startswith("confirm_delete_"):
            # Confirm deletion of reminder
            reminder_id = int(callback_data.replace("confirm_delete_", ""))
            reminder_data = self.db.get_reminder(reminder_id)
            
            if not reminder_data:
                await query.edit_message_text(
                    "Reminder not found. It may have been deleted already.",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.warning(f"User {query.from_user.id} tried to delete non-existent reminder {reminder_id}")
                return
            
            await query.edit_message_text(
                f"Are you sure you want to delete this reminder?\n\n"
                f"*{reminder_data['title']}*",
                parse_mode='Markdown',
                reply_markup=get_yes_no_keyboard(f"delete_{reminder_id}")
            )
            logger.info(f"User {query.from_user.id} confirming deletion of reminder {reminder_id}")
            
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
                    logger.info(f"User {query.from_user.id} deleted reminder {reminder_id}")
                else:
                    await query.edit_message_text(
                        "❌ Failed to delete reminder. Please try again.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    logger.error(f"Failed to delete reminder {reminder_id} for user {query.from_user.id}")
            else:
                # User cancelled deletion
                await query.edit_message_text(
                    "Deletion cancelled.",
                    reply_markup=get_main_menu_keyboard()
                )
                logger.info(f"User {query.from_user.id} cancelled deletion of reminder {reminder_id}")
                
        elif callback_data.startswith("postpone_"):
            # Handle postpone action
            parts = callback_data.split('_')
            reminder_id = int(parts[1])
            
            if len(parts) == 2:
                # Show postpone options
                await query.edit_message_text(
                    "How long would you like to postpone this reminder?",
                    reply_markup=get_postpone_options_keyboard(reminder_id)
                )
                logger.info(f"User {query.from_user.id} selecting postpone options for reminder {reminder_id}")
            else:
                # Process postpone duration
                duration = parts[2]
                reminder_data = self.db.get_reminder(reminder_id)
                
                if not reminder_data:
                    await query.edit_message_text(
                        "Reminder not found. It may have been deleted.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    logger.warning(f"User {query.from_user.id} tried to postpone non-existent reminder {reminder_id}")
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
                    logger.info(f"User {query.from_user.id} postponed reminder {reminder_id} to {new_due_date}")
                else:
                    await query.edit_message_text(
                        "❌ Failed to postpone reminder. Please try again.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    logger.error(f"Failed to postpone reminder {reminder_id} for user {query.from_user.id}")
                    
        elif callback_data.startswith("change_priority_"):
            # Show priority selection for a reminder
            reminder_id = int(callback_data.replace("change_priority_", ""))
            
            # Store reminder ID in user data for later use
            context.user_data['priority_reminder_id'] = reminder_id
            
            await query.edit_message_text(
                "Select a new priority level:",
                reply_markup=get_priority_keyboard()
            )
            logger.info(f"User {query.from_user.id} changing priority for reminder {reminder_id}")
            
        elif callback_data.startswith("priority_"):
            # Process priority selection for a reminder
            priority = callback_data.replace("priority_", "")
            
            # Check if we're updating an existing reminder
            reminder_id = context.user_data.get('priority_reminder_id')
            
            if reminder_id:
                # Update reminder priority
                success = self.db.update_reminder(reminder_id, priority=priority)
                
                if success:
                    await query.edit_message_text(
                        f"✅ Priority updated to {priority.capitalize()}!",
                        reply_markup=get_main_menu_keyboard()
                    )
                    logger.info(f"User {query.from_user.id} updated priority to {priority} for reminder {reminder_id}")
                else:
                    await query.edit_message_text(
                        "❌ Failed to update priority. Please try again.",
                        reply_markup=get_main_menu_keyboard()
                    )
                    logger.error(f"Failed to update priority for reminder {reminder_id} for user {query.from_user.id}")
                
                # Clear user data
                context.user_data.pop('priority_reminder_id', None)
            else:
                # We're in the add reminder flow
                context.user_data['reminder_priority'] = priority
                
                # Ask if recurring
                await query.edit_message_text(
                    f"Priority: *{priority.capitalize()}*\n\n"
                    f"Is this a recurring reminder?",
                    parse_mode='Markdown',
                    reply_markup=get_yes_no_keyboard('recurring')
                )
                logger.info(f"User {query.from_user.id} selected priority {priority} for new reminder")
                return ADD_RECURRING
                
        elif callback_data.startswith("recurring_"):
            # Process recurring selection
            recurring_type = callback_data.replace("recurring_", "")
            
            if recurring_type in ['yes', 'no']:
                # We're in the add reminder flow asking if recurring
                is_recurring = recurring_type == 'yes'
                
                if is_recurring:
                    # Ask for recurring pattern
                    await query.edit_message_text(
                        "Please select a recurrence pattern:",
                        reply_markup=get_recurring_options_keyboard()
                    )
                    logger.info(f"User {query.from_user.id} selected recurring for new reminder")
                    return RECURRING_SETUP
                else:
                    # Not recurring, save the reminder
                    return await self.save_reminder(update, context)
            else:
                # We're selecting a recurring pattern
                context.user_data['reminder_is_recurring'] = True
                context.user_data['reminder_recurrence_pattern'] = {'type': recurring_type}
                
                # Save the reminder
                return await self.save_reminder(update, context)
                
        elif callback_data.startswith("category_"):
            # Process category selection
            category = callback_data.replace('category_', '')
            
            # Store category in user data
            context.user_data['reminder_category'] = category
            
            # Ask for priority
            await query.edit_message_text(
                f"Category: *{category}*\n\n"
                f"Please select a priority level:",
                parse_mode='Markdown',
                reply_markup=get_priority_keyboard()
            )
            logger.info(f"User {query.from_user.id} selected category {category} for new reminder")
            return ADD_PRIORITY
            
        elif callback_data == "back_to_list":
            # Return to reminders list
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
            
            await query.edit_message_text(
                reminders_text,
                parse_mode='Markdown',
                reply_markup=get_reminders_list_keyboard(reminders)
            )
            logger.info(f"User {user_id} returned to reminders list")
    
    async def save_reminder(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Save the reminder to the database.
        
        Args:
            update (Update): Update object
            context (ContextTypes.DEFAULT_TYPE): Context object
            
        Returns:
            int: ConversationHandler.END to end the conversation
        """
        query = update.callback_query
        
        # Get user data
        user_id = query.from_user.id
        title = context.user_data.get('reminder_title')
        description = context.user_data.get('reminder_description')
        due_date = context.user_data.get('reminder_due_date')
        category = context.user_data.get('reminder_category')
        priority = context.user_data.get('reminder_priority')
        is_recurring = context.user_data.get('reminder_is_recurring', False)
        recurrence_pattern = context.user_data.get('reminder_recurrence_pattern')
        
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
            logger.info(f"User {user_id} created reminder {reminder_id}: {title}")
        else:
            # Error message
            await query.edit_message_text(
                "❌ Failed to create reminder. Please try again.",
                reply_markup=get_main_menu_keyboard()
            )
            logger.error(f"Failed to create reminder for user {user_id}")
        
        # Clear user data
        context.user_data.clear()
        return ConversationHandler.END
