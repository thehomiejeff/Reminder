"""
Reminder scheduler for ReminderBot.
Handles scheduling and management of reminders.
"""
from datetime import datetime, timedelta
import json
import pytz
# Import Reminder directly to avoid circular imports
from src.models.reminder import Reminder
from src.utils.logger import logger
from src.config import DEFAULT_TIMEZONE

class ReminderScheduler:
    """Reminder scheduler for ReminderBot."""
    
    def __init__(self, db):
        """
        Initialize the reminder scheduler.
        
        Args:
            db: Database instance
        """
        self.db = db
    
    def schedule_reminder(self, user_id, title, description=None, due_date=None, 
                         category=None, priority='medium', is_recurring=False, 
                         recurrence_pattern=None):
        """
        Schedule a new reminder.
        
        Args:
            user_id (int): Telegram user ID
            title (str): Reminder title
            description (str, optional): Reminder description
            due_date (datetime, optional): Due date and time
            category (str, optional): Reminder category
            priority (str, optional): Priority level (high, medium, low)
            is_recurring (bool, optional): Whether the reminder is recurring
            recurrence_pattern (dict, optional): Recurrence pattern details
            
        Returns:
            int: ID of the new reminder, or None if failed
        """
        # Convert recurrence pattern to JSON string if it's a dict
        if recurrence_pattern and isinstance(recurrence_pattern, dict):
            recurrence_pattern = json.dumps(recurrence_pattern)
        
        # Add reminder to database
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
            logger.info(f"Scheduled reminder {reminder_id} for user {user_id}")
        else:
            logger.error(f"Failed to schedule reminder for user {user_id}")
        
        return reminder_id
    
    def reschedule_reminder(self, reminder_id, new_due_date):
        """
        Reschedule an existing reminder.
        
        Args:
            reminder_id (int): Reminder ID
            new_due_date (datetime): New due date and time
            
        Returns:
            bool: True if successful, False otherwise
        """
        success = self.db.update_reminder(reminder_id, due_date=new_due_date)
        
        if success:
            logger.info(f"Rescheduled reminder {reminder_id} to {new_due_date}")
        else:
            logger.error(f"Failed to reschedule reminder {reminder_id}")
        
        return success
    
    def postpone_reminder(self, reminder_id, duration_type):
        """
        Postpone a reminder by a specified duration.
        
        Args:
            reminder_id (int): Reminder ID
            duration_type (str): Duration type ('1h', '3h', '1d', '1w')
            
        Returns:
            bool: True if successful, False otherwise
        """
        # Get current reminder
        reminder_data = self.db.get_reminder(reminder_id)
        if not reminder_data:
            logger.error(f"Reminder {reminder_id} not found for postponing")
            return False
        
        # Convert to Reminder object
        reminder = Reminder.from_dict(reminder_data)
        
        # Calculate new due date
        current_due_date = reminder.due_date or datetime.now()
        
        # Apply postpone duration
        if duration_type == '1h':
            new_due_date = current_due_date + timedelta(hours=1)
        elif duration_type == '3h':
            new_due_date = current_due_date + timedelta(hours=3)
        elif duration_type == '1d':
            new_due_date = current_due_date + timedelta(days=1)
        elif duration_type == '1w':
            new_due_date = current_due_date + timedelta(weeks=1)
        else:
            logger.error(f"Invalid postpone duration: {duration_type}")
            return False
        
        # Update reminder
        return self.reschedule_reminder(reminder_id, new_due_date)
    
    def change_reminder_priority(self, reminder_id, new_priority):
        """
        Change the priority of a reminder.
        
        Args:
            reminder_id (int): Reminder ID
            new_priority (str): New priority level (high, medium, low)
            
        Returns:
            bool: True if successful, False otherwise
        """
        if new_priority not in ['high', 'medium', 'low']:
            logger.error(f"Invalid priority level: {new_priority}")
            return False
        
        success = self.db.update_reminder(reminder_id, priority=new_priority)
        
        if success:
            logger.info(f"Changed priority of reminder {reminder_id} to {new_priority}")
        else:
            logger.error(f"Failed to change priority of reminder {reminder_id}")
        
        return success
    
    def change_reminder_category(self, reminder_id, new_category):
        """
        Change the category of a reminder.
        
        Args:
            reminder_id (int): Reminder ID
            new_category (str): New category
            
        Returns:
            bool: True if successful, False otherwise
        """
        success = self.db.update_reminder(reminder_id, category=new_category)
        
        if success:
            logger.info(f"Changed category of reminder {reminder_id} to {new_category}")
        else:
            logger.error(f"Failed to change category of reminder {reminder_id}")
        
        return success
    
    def mark_reminder_completed(self, reminder_id, completed=True):
        """
        Mark a reminder as completed or not completed.
        
        Args:
            reminder_id (int): Reminder ID
            completed (bool, optional): Completion status
            
        Returns:
            bool: True if successful, False otherwise
        """
        success = self.db.mark_reminder_completed(reminder_id, completed)
        
        if success:
            status = "completed" if completed else "not completed"
            logger.info(f"Marked reminder {reminder_id} as {status}")
        else:
            logger.error(f"Failed to mark reminder {reminder_id} as completed")
        
        return success
    
    def delete_reminder(self, reminder_id):
        """
        Delete a reminder.
        
        Args:
            reminder_id (int): Reminder ID
            
        Returns:
            bool: True if successful, False otherwise
        """
        success = self.db.delete_reminder(reminder_id)
        
        if success:
            logger.info(f"Deleted reminder {reminder_id}")
        else:
            logger.error(f"Failed to delete reminder {reminder_id}")
        
        return success
    
    def get_reminders_by_category(self, user_id, category):
        """
        Get reminders for a user filtered by category.
        
        Args:
            user_id (int): Telegram user ID
            category (str): Category to filter by
            
        Returns:
            list: List of Reminder objects
        """
        reminders_data = self.db.get_reminders_by_category(user_id, category)
        reminders = [Reminder.from_dict(r) for r in reminders_data]
        
        logger.info(f"Retrieved {len(reminders)} reminders in category '{category}' for user {user_id}")
        return reminders
    
    def get_reminders_by_priority(self, user_id, priority):
        """
        Get reminders for a user filtered by priority.
        
        Args:
            user_id (int): Telegram user ID
            priority (str): Priority to filter by
            
        Returns:
            list: List of Reminder objects
        """
        # Get all reminders for the user
        reminders_data = self.db.get_reminders(user_id)
        
        # Filter by priority
        filtered_data = [r for r in reminders_data if r.get('priority') == priority]
        reminders = [Reminder.from_dict(r) for r in filtered_data]
        
        logger.info(f"Retrieved {len(reminders)} reminders with priority '{priority}' for user {user_id}")
        return reminders
    
    def get_due_reminders(self, user_id):
        """
        Get reminders that are due now or in the past.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            list: List of Reminder objects
        """
        reminders_data = self.db.get_due_reminders(user_id)
        reminders = [Reminder.from_dict(r) for r in reminders_data]
        
        logger.info(f"Retrieved {len(reminders)} due reminders for user {user_id}")
        return reminders
    
    def calculate_next_occurrence(self, reminder):
        """
        Calculate the next occurrence date for a recurring reminder.
        
        Args:
            reminder (Reminder): Reminder object
            
        Returns:
            datetime: Next occurrence date or None if no more occurrences
        """
        if not reminder.is_recurring or not reminder.recurrence_pattern:
            return None
        
        # Parse recurrence pattern
        if isinstance(reminder.recurrence_pattern, str):
            try:
                pattern = json.loads(reminder.recurrence_pattern)
            except json.JSONDecodeError:
                logger.error(f"Invalid recurrence pattern for reminder {reminder.id}")
                return None
        else:
            pattern = reminder.recurrence_pattern
        
        # Get current due date
        current_date = reminder.due_date or datetime.now()
        
        # Calculate next date based on pattern type
        if pattern.get('type') == 'daily':
            return current_date + timedelta(days=1)
            
        elif pattern.get('type') == 'weekly':
            days = pattern.get('days', [])
            if not days:
                # If no specific days, just add 7 days
                return current_date + timedelta(days=7)
            
            # Get current weekday (0-6, where 0 is Monday)
            current_weekday = current_date.weekday()
            
            # Find the next weekday in the list
            next_day = None
            for day in sorted(days):
                if day > current_weekday:
                    next_day = day
                    break
            
            # If no next day found, wrap around to the first day in the list
            if next_day is None:
                next_day = min(days)
                # Add a week
                days_to_add = 7 - current_weekday + next_day
            else:
                days_to_add = next_day - current_weekday
            
            return current_date + timedelta(days=days_to_add)
            
        elif pattern.get('type') == 'monthly':
            # Get the day of month to use
            day = pattern.get('day', current_date.day)
            
            # Create a date for next month, same day
            next_month = current_date.replace(day=1)
            if next_month.month == 12:
                next_month = next_month.replace(year=next_month.year + 1, month=1)
            else:
                next_month = next_month.replace(month=next_month.month + 1)
            
            # Adjust the day if necessary (e.g., if the month doesn't have that day)
            import calendar
            last_day = calendar.monthrange(next_month.year, next_month.month)[1]
            day = min(day, last_day)
            
            return next_month.replace(day=day)
            
        elif pattern.get('type') == 'custom':
            # For custom patterns, we would need more logic
            # For now, just add a week as default
            return current_date + timedelta(weeks=1)
        
        return None
