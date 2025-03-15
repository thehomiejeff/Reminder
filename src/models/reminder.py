"""
Reminder model for ReminderBot.
Defines the Reminder class for managing reminder objects.
"""
from datetime import datetime
import json

class Reminder:
    """Reminder class for managing reminder objects."""
    
    def __init__(self, id=None, user_id=None, title=None, description=None, 
                 due_date=None, category=None, priority='medium', 
                 is_recurring=False, recurrence_pattern=None, is_completed=False,
                 created_at=None):
        """
        Initialize a Reminder object.
        
        Args:
            id (int, optional): Reminder ID
            user_id (int, optional): Telegram user ID
            title (str, optional): Reminder title
            description (str, optional): Reminder description
            due_date (datetime, optional): Due date and time
            category (str, optional): Reminder category
            priority (str, optional): Priority level (high, medium, low)
            is_recurring (bool, optional): Whether the reminder is recurring
            recurrence_pattern (str, optional): JSON string with recurrence details
            is_completed (bool, optional): Whether the reminder is completed
            created_at (datetime, optional): Creation timestamp
        """
        self.id = id
        self.user_id = user_id
        self.title = title
        self.description = description
        self.due_date = due_date
        self.category = category
        self.priority = priority
        self.is_recurring = is_recurring
        self.recurrence_pattern = recurrence_pattern
        self.is_completed = is_completed
        self.created_at = created_at or datetime.now()
    
    @classmethod
    def from_dict(cls, data):
        """
        Create a Reminder object from a dictionary.
        
        Args:
            data (dict): Dictionary containing reminder data
        
        Returns:
            Reminder: New Reminder object
        """
        # Convert string due_date to datetime if it exists
        if 'due_date' in data and data['due_date']:
            if isinstance(data['due_date'], str):
                data['due_date'] = datetime.fromisoformat(data['due_date'].replace('Z', '+00:00'))
        
        # Convert string created_at to datetime if it exists
        if 'created_at' in data and data['created_at']:
            if isinstance(data['created_at'], str):
                data['created_at'] = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        # Convert recurrence_pattern from JSON string if needed
        if 'recurrence_pattern' in data and data['recurrence_pattern']:
            if isinstance(data['recurrence_pattern'], str):
                try:
                    data['recurrence_pattern'] = json.loads(data['recurrence_pattern'])
                except json.JSONDecodeError:
                    pass  # Keep as string if not valid JSON
        
        return cls(**data)
    
    def to_dict(self):
        """
        Convert Reminder object to dictionary.
        
        Returns:
            dict: Dictionary representation of the reminder
        """
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'description': self.description,
            'category': self.category,
            'priority': self.priority,
            'is_recurring': self.is_recurring,
            'is_completed': self.is_completed
        }
        
        # Convert datetime objects to strings
        if self.due_date:
            data['due_date'] = self.due_date.isoformat()
        
        if self.created_at:
            data['created_at'] = self.created_at.isoformat()
        
        # Convert recurrence_pattern to JSON string if it's a dict
        if self.recurrence_pattern:
            if isinstance(self.recurrence_pattern, dict):
                data['recurrence_pattern'] = json.dumps(self.recurrence_pattern)
            else:
                data['recurrence_pattern'] = self.recurrence_pattern
        
        return data
    
    def get_formatted_due_date(self, format_str='%Y-%m-%d %H:%M'):
        """
        Get formatted due date string.
        
        Args:
            format_str (str, optional): Date format string
        
        Returns:
            str: Formatted date string or empty string if no due date
        """
        if self.due_date:
            return self.due_date.strftime(format_str)
        return ''
    
    def get_priority_emoji(self):
        """
        Get emoji representation of priority.
        
        Returns:
            str: Emoji string
        """
        priority_map = {
            'high': '⚠️',
            'medium': '⚡',
            'low': '✓'
        }
        return priority_map.get(self.priority, '✓')
    
    def is_due(self):
        """
        Check if reminder is due (due date is in the past).
        
        Returns:
            bool: True if due, False otherwise
        """
        if not self.due_date:
            return False
        return self.due_date <= datetime.now()
    
    def get_recurrence_text(self):
        """
        Get human-readable recurrence pattern text.
        
        Returns:
            str: Recurrence description or empty string if not recurring
        """
        if not self.is_recurring or not self.recurrence_pattern:
            return ''
        
        # Parse recurrence pattern
        if isinstance(self.recurrence_pattern, str):
            try:
                pattern = json.loads(self.recurrence_pattern)
            except json.JSONDecodeError:
                return 'Recurring'
        else:
            pattern = self.recurrence_pattern
        
        # Generate human-readable text based on pattern
        if pattern.get('type') == 'daily':
            return 'Every day'
        elif pattern.get('type') == 'weekly':
            days = pattern.get('days', [])
            if len(days) == 7:
                return 'Every day'
            elif len(days) == 0:
                return 'Weekly'
            else:
                day_names = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
                day_texts = [day_names[day] for day in days]
                return f"Weekly on {', '.join(day_texts)}"
        elif pattern.get('type') == 'monthly':
            day = pattern.get('day')
            return f'Monthly on day {day}' if day else 'Monthly'
        elif pattern.get('type') == 'custom':
            return pattern.get('description', 'Custom schedule')
        
        return 'Recurring'
    
    def __str__(self):
        """
        Get string representation of reminder.
        
        Returns:
            str: String representation
        """
        priority = self.get_priority_emoji()
        due_date = self.get_formatted_due_date() if self.due_date else 'No due date'
        recurring = f" (🔄 {self.get_recurrence_text()})" if self.is_recurring else ""
        category = f" [{self.category}]" if self.category else ""
        
        return f"{priority} {self.title}{category} - {due_date}{recurring}"
