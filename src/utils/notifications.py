"""
Notification manager for ReminderBot.
Handles sending reminder notifications to users.
"""
from datetime import datetime
import asyncio
from telegram import Bot
# Import Reminder directly to avoid circular imports
from src.models.reminder import Reminder
from src.utils.logger import logger
from src.utils.keyboards import get_reminder_actions_keyboard

class NotificationManager:
    """Notification manager for ReminderBot."""
    
    def __init__(self, bot: Bot, db):
        """
        Initialize the notification manager.
        
        Args:
            bot (Bot): Telegram Bot instance
            db: Database instance
        """
        self.bot = bot
        self.db = db
        self.is_running = False
        self.check_interval = 60  # Check for due reminders every 60 seconds
    
    async def start(self):
        """Start the notification manager."""
        self.is_running = True
        logger.info("Notification manager started")
        await self._notification_loop()
    
    async def stop(self):
        """Stop the notification manager."""
        self.is_running = False
        logger.info("Notification manager stopped")
    
    async def _notification_loop(self):
        """Main notification loop."""
        while self.is_running:
            try:
                await self._check_due_reminders()
                await asyncio.sleep(self.check_interval)
            except Exception as e:
                logger.error(f"Error in notification loop: {e}", exc_info=True)
                await asyncio.sleep(self.check_interval)
    
    async def _check_due_reminders(self):
        """Check for due reminders and send notifications."""
        # Get all users
        users = self.db.get_all_users()
        
        for user in users:
            user_id = user['user_id']
            
            # Get due reminders for this user
            due_reminders = self.db.get_due_reminders(user_id)
            
            for reminder_data in due_reminders:
                reminder = Reminder.from_dict(reminder_data)
                
                # Skip if already notified (would be tracked in a real implementation)
                # For now, we'll just send a notification
                
                # Send notification
                await self._send_reminder_notification(user_id, reminder)
                
                # Update reminder if recurring
                if reminder.is_recurring:
                    # Calculate next occurrence (simplified)
                    # In a real implementation, this would use the recurrence pattern
                    # to calculate the next occurrence date
                    next_date = self._calculate_next_occurrence(reminder)
                    
                    if next_date:
                        # Update reminder with new due date
                        self.db.update_reminder(reminder.id, due_date=next_date)
                        logger.info(f"Updated recurring reminder {reminder.id} with next date {next_date}")
                else:
                    # Mark non-recurring reminder as completed
                    self.db.mark_reminder_completed(reminder.id)
                    logger.info(f"Marked reminder {reminder.id} as completed after notification")
    
    async def _send_reminder_notification(self, user_id, reminder):
        """
        Send a reminder notification to a user.
        
        Args:
            user_id (int): Telegram user ID
            reminder (Reminder): Reminder object
        """
        try:
            # Format notification message
            message = (
                f"🔔 *Reminder: {reminder.title}*\n\n"
                f"Category: {reminder.category}\n"
                f"Priority: {reminder.priority.capitalize()}\n"
            )
            
            if reminder.description:
                message += f"Description: {reminder.description}\n"
            
            # Send notification with action buttons
            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown',
                reply_markup=get_reminder_actions_keyboard(reminder.id)
            )
            
            logger.info(f"Sent reminder notification for reminder {reminder.id} to user {user_id}")
        except Exception as e:
            logger.error(f"Error sending notification to user {user_id}: {e}", exc_info=True)
    
    def _calculate_next_occurrence(self, reminder):
        """
        Calculate the next occurrence date for a recurring reminder.
        
        Args:
            reminder (Reminder): Reminder object
            
        Returns:
            datetime: Next occurrence date or None if no more occurrences
        """
        # This is a simplified implementation
        # In a real bot, this would use the recurrence pattern to calculate
        # the next occurrence date based on the pattern type
        
        if not reminder.recurrence_pattern:
            return None
        
        # Parse recurrence pattern
        if isinstance(reminder.recurrence_pattern, str):
            import json
            try:
                pattern = json.loads(reminder.recurrence_pattern)
            except json.JSONDecodeError:
                return None
        else:
            pattern = reminder.recurrence_pattern
        
        # Get current due date
        current_date = reminder.due_date or datetime.now()
        
        # Calculate next date based on pattern type
        if pattern.get('type') == 'daily':
            from datetime import timedelta
            return current_date + timedelta(days=1)
            
        elif pattern.get('type') == 'weekly':
            from datetime import timedelta
            return current_date + timedelta(weeks=1)
            
        elif pattern.get('type') == 'monthly':
            # Simple implementation - just add 30 days
            # A real implementation would be more sophisticated
            from datetime import timedelta
            return current_date + timedelta(days=30)
            
        elif pattern.get('type') == 'custom':
            # For custom patterns, we would need more logic
            # For now, just add a week as default
            from datetime import timedelta
            return current_date + timedelta(weeks=1)
        
        return None
