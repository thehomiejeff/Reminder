"""
Test script for ReminderBot.
Tests the functionality of the bot.
"""
import os
import sys
import unittest
from datetime import datetime, timedelta
import pytz
import json

# Add the parent directory to the path so we can import the src package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.database import Database
from src.models.reminder import Reminder
from src.utils.scheduler import ReminderScheduler
from src.utils.persistence import DataPersistenceManager
from src.config import REMINDER_CATEGORIES, PRIORITY_LEVELS

class TestReminderBot(unittest.TestCase):
    """Test cases for ReminderBot."""
    
    def setUp(self):
        """Set up test environment."""
        # Use a test database
        os.environ['DATABASE_PATH'] = 'data/test_reminderbot.db'
        
        # Initialize database
        self.db = Database()
        
        # Initialize scheduler
        self.scheduler = ReminderScheduler(self.db)
        
        # Initialize persistence manager
        self.persistence_manager = DataPersistenceManager(self.db, backup_dir='data/test_backups')
        
        # Create test user
        self.test_user_id = 123456789
        self.db.add_user(self.test_user_id, "Test", "User", "testuser")
    
    def tearDown(self):
        """Clean up after tests."""
        # Close database connection
        self.db.close()
        
        # Remove test database
        if os.path.exists('data/test_reminderbot.db'):
            os.remove('data/test_reminderbot.db')
        
        # Remove test backups
        if os.path.exists('data/test_backups'):
            import shutil
            shutil.rmtree('data/test_backups')
    
    def test_database_connection(self):
        """Test database connection."""
        self.assertIsNotNone(self.db.conn)
        self.assertIsNotNone(self.db.cursor)
    
    def test_add_user(self):
        """Test adding a user."""
        # Add a new user
        user_id = 987654321
        success = self.db.add_user(user_id, "Another", "User", "anotheruser")
        
        # Check if user was added
        self.assertTrue(success)
        
        # Get all users
        users = self.db.get_all_users()
        
        # Check if the new user is in the list
        user_ids = [user['user_id'] for user in users]
        self.assertIn(user_id, user_ids)
    
    def test_add_reminder(self):
        """Test adding a reminder."""
        # Add a reminder
        title = "Test Reminder"
        description = "This is a test reminder"
        due_date = datetime.now() + timedelta(days=1)
        category = REMINDER_CATEGORIES[0]
        priority = "high"
        
        reminder_id = self.scheduler.schedule_reminder(
            user_id=self.test_user_id,
            title=title,
            description=description,
            due_date=due_date,
            category=category,
            priority=priority
        )
        
        # Check if reminder was added
        self.assertIsNotNone(reminder_id)
        
        # Get the reminder
        reminder_data = self.db.get_reminder(reminder_id)
        
        # Check reminder data
        self.assertEqual(reminder_data['title'], title)
        self.assertEqual(reminder_data['description'], description)
        self.assertEqual(reminder_data['category'], category)
        self.assertEqual(reminder_data['priority'], priority)
    
    def test_get_reminders(self):
        """Test getting reminders for a user."""
        # Clear any existing reminders first
        reminders = self.db.get_reminders(self.test_user_id)
        for reminder in reminders:
            self.scheduler.delete_reminder(reminder['id'])
            
        # Verify we're starting with a clean slate
        reminders = self.db.get_reminders(self.test_user_id)
        self.assertEqual(len(reminders), 0)
        
        # Add exactly 3 reminders for this test
        for i in range(3):
            self.scheduler.schedule_reminder(
                user_id=self.test_user_id,
                title=f"Test Reminder {i+1}",
                description=f"This is test reminder {i+1}",
                due_date=datetime.now() + timedelta(days=i+1),
                category=REMINDER_CATEGORIES[i % len(REMINDER_CATEGORIES)],
                priority="medium"
            )
        
        # Get reminders
        reminders = self.db.get_reminders(self.test_user_id)
        
        # Check if we got the right number of reminders
        self.assertEqual(len(reminders), 3)
    
    def test_update_reminder(self):
        """Test updating a reminder."""
        # Add a reminder
        reminder_id = self.scheduler.schedule_reminder(
            user_id=self.test_user_id,
            title="Original Title",
            description="Original description",
            due_date=datetime.now() + timedelta(days=1),
            category=REMINDER_CATEGORIES[0],
            priority="medium"
        )
        
        # Update the reminder
        new_title = "Updated Title"
        success = self.db.update_reminder(reminder_id, title=new_title)
        
        # Check if update was successful
        self.assertTrue(success)
        
        # Get the updated reminder
        reminder_data = self.db.get_reminder(reminder_id)
        
        # Check if title was updated
        self.assertEqual(reminder_data['title'], new_title)
    
    def test_delete_reminder(self):
        """Test deleting a reminder."""
        # Add a reminder
        reminder_id = self.scheduler.schedule_reminder(
            user_id=self.test_user_id,
            title="Reminder to Delete",
            description="This reminder will be deleted",
            due_date=datetime.now() + timedelta(days=1),
            category=REMINDER_CATEGORIES[0],
            priority="medium"
        )
        
        # Delete the reminder
        success = self.scheduler.delete_reminder(reminder_id)
        
        # Check if deletion was successful
        self.assertTrue(success)
        
        # Try to get the deleted reminder
        reminder_data = self.db.get_reminder(reminder_id)
        
        # Check if reminder is gone
        self.assertIsNone(reminder_data)
    
    def test_mark_reminder_completed(self):
        """Test marking a reminder as completed."""
        # Add a reminder
        reminder_id = self.scheduler.schedule_reminder(
            user_id=self.test_user_id,
            title="Reminder to Complete",
            description="This reminder will be marked as completed",
            due_date=datetime.now() + timedelta(days=1),
            category=REMINDER_CATEGORIES[0],
            priority="medium"
        )
        
        # Mark as completed
        success = self.scheduler.mark_reminder_completed(reminder_id)
        
        # Check if operation was successful
        self.assertTrue(success)
        
        # Get the reminder
        reminder_data = self.db.get_reminder(reminder_id)
        
        # Check if it's marked as completed
        self.assertTrue(reminder_data['is_completed'])
    
    def test_recurring_reminder(self):
        """Test recurring reminder functionality."""
        # Add a recurring reminder
        recurrence_pattern = {'type': 'daily'}
        
        reminder_id = self.scheduler.schedule_reminder(
            user_id=self.test_user_id,
            title="Recurring Reminder",
            description="This is a recurring reminder",
            due_date=datetime.now(),
            category=REMINDER_CATEGORIES[0],
            priority="medium",
            is_recurring=True,
            recurrence_pattern=recurrence_pattern
        )
        
        # Get the reminder
        reminder_data = self.db.get_reminder(reminder_id)
        reminder = Reminder.from_dict(reminder_data)
        
        # Calculate next occurrence
        next_date = self.scheduler.calculate_next_occurrence(reminder)
        
        # Check if next date is about 1 day later
        self.assertIsNotNone(next_date)
        
        # Allow for small time differences
        time_diff = next_date - reminder.due_date
        self.assertGreaterEqual(time_diff.total_seconds(), 86000)  # Just under 24 hours
        self.assertLessEqual(time_diff.total_seconds(), 86500)  # Just over 24 hours
    
    def test_backup_restore(self):
        """Test backup and restore functionality."""
        # Add a reminder
        reminder_id = self.scheduler.schedule_reminder(
            user_id=self.test_user_id,
            title="Reminder for Backup",
            description="This reminder will be backed up",
            due_date=datetime.now() + timedelta(days=1),
            category=REMINDER_CATEGORIES[0],
            priority="medium"
        )
        
        # Ensure the backup directory exists
        os.makedirs('data/test_backups', exist_ok=True)
        
        # Create backup
        backup_path = self.persistence_manager.backup_database()
        
        # Check if backup was created
        self.assertIsNotNone(backup_path)
        self.assertTrue(os.path.exists(backup_path))
        
        # Delete the reminder
        self.scheduler.delete_reminder(reminder_id)
        
        # Check if reminder is gone
        self.assertIsNone(self.db.get_reminder(reminder_id))
        
        # Restore from backup
        success = self.persistence_manager.restore_database(backup_path)
        
        # Check if restore was successful
        self.assertTrue(success)
        
        # Reconnect to database
        self.db.connect()
        
        # Check if reminder is back
        reminder_data = self.db.get_reminder(reminder_id)
        self.assertIsNotNone(reminder_data)
        self.assertEqual(reminder_data['title'], "Reminder for Backup")
    
    def test_export_import_user_data(self):
        """Test exporting and importing user data."""
        # Clear any existing reminders first
        reminders = self.db.get_reminders(self.test_user_id)
        for reminder in reminders:
            self.scheduler.delete_reminder(reminder['id'])
            
        # Verify we're starting with a clean slate
        reminders = self.db.get_reminders(self.test_user_id)
        self.assertEqual(len(reminders), 0)
        
        # Add exactly 3 reminders for this test
        for i in range(3):
            self.scheduler.schedule_reminder(
                user_id=self.test_user_id,
                title=f"Export Test Reminder {i+1}",
                description=f"This reminder will be exported",
                due_date=datetime.now() + timedelta(days=i+1),
                category=REMINDER_CATEGORIES[i % len(REMINDER_CATEGORIES)],
                priority="medium"
            )
        
        # Ensure the backup directory exists
        os.makedirs('data/test_backups', exist_ok=True)
        
        # Export user data
        export_path = self.persistence_manager.export_user_data(self.test_user_id)
        
        # Check if export was created
        self.assertIsNotNone(export_path)
        self.assertTrue(os.path.exists(export_path))
        
        # Delete all reminders
        reminders = self.db.get_reminders(self.test_user_id)
        for reminder in reminders:
            self.scheduler.delete_reminder(reminder['id'])
        
        # Check if reminders are gone
        reminders = self.db.get_reminders(self.test_user_id)
        self.assertEqual(len(reminders), 0)
        
        # Import user data
        success = self.persistence_manager.import_user_data(export_path)
        
        # Check if import was successful
        self.assertTrue(success)
        
        # Check if reminders are back - we only care that the specific test reminders are there
        reminders = self.db.get_reminders(self.test_user_id)
        
        # Check if titles are correct
        titles = [r['title'] for r in reminders]
        for i in range(3):
            self.assertIn(f"Export Test Reminder {i+1}", titles)

if __name__ == '__main__':
    unittest.main()
