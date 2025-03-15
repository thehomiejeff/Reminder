"""
Database module for ReminderBot.
Handles database operations for storing and retrieving reminders.
"""
import sqlite3
import json
import os
from datetime import datetime
from src.utils.logger import logger
from src.config import DATABASE_PATH

class Database:
    """Database handler for ReminderBot."""
    
    def __init__(self):
        """Initialize the database connection and create tables if they don't exist."""
        # Ensure the directory exists
        os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
        
        self.conn = None
        self.cursor = None
        self.connect()
        self.create_tables()
    
    def connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(DATABASE_PATH)
            self.conn.row_factory = sqlite3.Row  # Return rows as dictionaries
            self.cursor = self.conn.cursor()
            logger.info("Connected to database successfully")
        except sqlite3.Error as e:
            logger.error(f"Database connection error: {e}")
            raise
    
    def create_tables(self):
        """Create necessary tables if they don't exist."""
        try:
            # Create users table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                first_name TEXT,
                last_name TEXT,
                username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
            ''')
            
            # Create reminders table
            self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                title TEXT NOT NULL,
                description TEXT,
                due_date TIMESTAMP,
                category TEXT,
                priority TEXT DEFAULT 'medium',
                is_recurring BOOLEAN DEFAULT 0,
                recurrence_pattern TEXT,
                is_completed BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(user_id)
            )
            ''')
            
            self.conn.commit()
            logger.info("Database tables created successfully")
        except sqlite3.Error as e:
            logger.error(f"Error creating tables: {e}")
            raise
    
    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            logger.info("Database connection closed")
    
    def add_user(self, user_id, first_name, last_name=None, username=None):
        """
        Add a new user or update existing user.
        
        Args:
            user_id (int): Telegram user ID
            first_name (str): User's first name
            last_name (str, optional): User's last name
            username (str, optional): User's username
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cursor.execute('''
            INSERT OR REPLACE INTO users (user_id, first_name, last_name, username)
            VALUES (?, ?, ?, ?)
            ''', (user_id, first_name, last_name, username))
            self.conn.commit()
            logger.info(f"User {user_id} added/updated successfully")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error adding user: {e}")
            return False
    
    def add_reminder(self, user_id, title, description=None, due_date=None, 
                    category=None, priority='medium', is_recurring=False, 
                    recurrence_pattern=None):
        """
        Add a new reminder.
        
        Args:
            user_id (int): Telegram user ID
            title (str): Reminder title
            description (str, optional): Reminder description
            due_date (datetime, optional): Due date and time
            category (str, optional): Reminder category
            priority (str, optional): Priority level (high, medium, low)
            is_recurring (bool, optional): Whether the reminder is recurring
            recurrence_pattern (str, optional): JSON string with recurrence details
        
        Returns:
            int: ID of the new reminder, or None if failed
        """
        try:
            self.cursor.execute('''
            INSERT INTO reminders (
                user_id, title, description, due_date, category, 
                priority, is_recurring, recurrence_pattern
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, title, description, due_date, category,
                priority, is_recurring, recurrence_pattern
            ))
            self.conn.commit()
            reminder_id = self.cursor.lastrowid
            logger.info(f"Reminder {reminder_id} added successfully for user {user_id}")
            return reminder_id
        except sqlite3.Error as e:
            logger.error(f"Error adding reminder: {e}")
            return None
    
    def get_reminders(self, user_id, include_completed=False):
        """
        Get all reminders for a user.
        
        Args:
            user_id (int): Telegram user ID
            include_completed (bool, optional): Whether to include completed reminders
        
        Returns:
            list: List of reminder dictionaries
        """
        try:
            query = '''
            SELECT * FROM reminders 
            WHERE user_id = ?
            '''
            
            if not include_completed:
                query += ' AND is_completed = 0'
                
            query += ' ORDER BY due_date ASC'
            
            self.cursor.execute(query, (user_id,))
            reminders = [dict(row) for row in self.cursor.fetchall()]
            logger.info(f"Retrieved {len(reminders)} reminders for user {user_id}")
            return reminders
        except sqlite3.Error as e:
            logger.error(f"Error getting reminders: {e}")
            return []
    
    def get_reminder(self, reminder_id):
        """
        Get a specific reminder by ID.
        
        Args:
            reminder_id (int): Reminder ID
        
        Returns:
            dict: Reminder data or None if not found
        """
        try:
            self.cursor.execute('SELECT * FROM reminders WHERE id = ?', (reminder_id,))
            reminder = self.cursor.fetchone()
            if reminder:
                return dict(reminder)
            return None
        except sqlite3.Error as e:
            logger.error(f"Error getting reminder {reminder_id}: {e}")
            return None
    
    def update_reminder(self, reminder_id, **kwargs):
        """
        Update a reminder.
        
        Args:
            reminder_id (int): Reminder ID
            **kwargs: Fields to update
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Build the SET part of the query dynamically
            set_clause = ', '.join([f"{key} = ?" for key in kwargs.keys()])
            values = list(kwargs.values())
            values.append(reminder_id)
            
            query = f"UPDATE reminders SET {set_clause} WHERE id = ?"
            self.cursor.execute(query, values)
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"Reminder {reminder_id} updated successfully")
                return True
            else:
                logger.warning(f"No reminder found with ID {reminder_id}")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error updating reminder {reminder_id}: {e}")
            return False
    
    def delete_reminder(self, reminder_id):
        """
        Delete a reminder.
        
        Args:
            reminder_id (int): Reminder ID
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
            self.conn.commit()
            
            if self.cursor.rowcount > 0:
                logger.info(f"Reminder {reminder_id} deleted successfully")
                return True
            else:
                logger.warning(f"No reminder found with ID {reminder_id}")
                return False
        except sqlite3.Error as e:
            logger.error(f"Error deleting reminder {reminder_id}: {e}")
            return False
    
    def mark_reminder_completed(self, reminder_id, completed=True):
        """
        Mark a reminder as completed or not completed.
        
        Args:
            reminder_id (int): Reminder ID
            completed (bool, optional): Completion status
        
        Returns:
            bool: True if successful, False otherwise
        """
        return self.update_reminder(reminder_id, is_completed=completed)
    
    def get_reminders_by_category(self, user_id, category):
        """
        Get reminders for a user filtered by category.
        
        Args:
            user_id (int): Telegram user ID
            category (str): Category to filter by
        
        Returns:
            list: List of reminder dictionaries
        """
        try:
            self.cursor.execute('''
            SELECT * FROM reminders 
            WHERE user_id = ? AND category = ? AND is_completed = 0
            ORDER BY due_date ASC
            ''', (user_id, category))
            
            reminders = [dict(row) for row in self.cursor.fetchall()]
            logger.info(f"Retrieved {len(reminders)} reminders in category '{category}' for user {user_id}")
            return reminders
        except sqlite3.Error as e:
            logger.error(f"Error getting reminders by category: {e}")
            return []
    
    def get_due_reminders(self, user_id):
        """
        Get reminders that are due now or in the past.
        
        Args:
            user_id (int): Telegram user ID
        
        Returns:
            list: List of reminder dictionaries
        """
        try:
            now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            self.cursor.execute('''
            SELECT * FROM reminders 
            WHERE user_id = ? AND due_date <= ? AND is_completed = 0
            ORDER BY due_date ASC
            ''', (user_id, now))
            
            reminders = [dict(row) for row in self.cursor.fetchall()]
            logger.info(f"Retrieved {len(reminders)} due reminders for user {user_id}")
            return reminders
        except sqlite3.Error as e:
            logger.error(f"Error getting due reminders: {e}")
            return []
            
    def get_all_users(self):
        """
        Get all users in the database.
        
        Returns:
            list: List of user dictionaries
        """
        try:
            self.cursor.execute('SELECT * FROM users')
            users = [dict(row) for row in self.cursor.fetchall()]
            logger.info(f"Retrieved {len(users)} users from database")
            return users
        except sqlite3.Error as e:
            logger.error(f"Error getting users: {e}")
            return []
