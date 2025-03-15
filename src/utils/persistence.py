"""
Data persistence manager for ReminderBot.
Handles data backup and restoration.
"""
import os
import json
import sqlite3
import shutil
from datetime import datetime
from src.utils.logger import logger

class DataPersistenceManager:
    """Data persistence manager for ReminderBot."""
    
    def __init__(self, db, backup_dir='data/backups'):
        """
        Initialize the data persistence manager.
        
        Args:
            db: Database instance
            backup_dir (str, optional): Directory for backups
        """
        self.db = db
        self.backup_dir = backup_dir
        
        # Ensure backup directory exists
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def backup_database(self):
        """
        Create a backup of the database.
        
        Returns:
            str: Path to the backup file or None if failed
        """
        try:
            # Get database path from the database instance
            db_path = self.db.conn.path if hasattr(self.db.conn, 'path') else ':memory:'
            
            # If we're using an in-memory database for tests, create a temporary file
            if db_path == ':memory:':
                # Create a temporary file with the database contents
                import tempfile
                temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.db')
                temp_db_path = temp_db.name
                temp_db.close()
                
                # Create a new connection to the temporary file
                temp_conn = sqlite3.connect(temp_db_path)
                
                # Export the in-memory database to the temporary file
                self.db.conn.backup(temp_conn)
                temp_conn.close()
                
                # Use the temporary file as the source for backup
                db_path = temp_db_path
            
            # Create backup filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_filename = f"reminderbot_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_filename)
            
            # Ensure backup directory exists
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Create backup
            shutil.copy2(db_path, backup_path)
            
            # Clean up temporary file if created
            if db_path.endswith('.db') and db_path.startswith('/tmp/'):
                os.unlink(db_path)
            
            logger.info(f"Database backup created at {backup_path}")
            return backup_path
        except Exception as e:
            logger.error(f"Error creating database backup: {e}", exc_info=True)
            return None
    
    def restore_database(self, backup_path):
        """
        Restore database from a backup.
        
        Args:
            backup_path (str): Path to the backup file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # For in-memory databases, we need to restore differently
            if not hasattr(self.db.conn, 'path') or self.db.conn.path == ':memory:':
                # Close current database connection
                self.db.close()
                
                # Create a new connection to the backup file
                backup_conn = sqlite3.connect(backup_path)
                
                # Reconnect to database (in-memory)
                self.db.connect()
                
                # Copy data from backup to in-memory database
                backup_conn.backup(self.db.conn)
                backup_conn.close()
            else:
                # Get database path
                db_path = self.db.conn.path
                
                # If we couldn't get the path, use the default from config
                if not db_path:
                    from src.config import DATABASE_PATH
                    db_path = DATABASE_PATH
                
                # Close current database connection
                self.db.close()
                
                # Restore from backup
                shutil.copy2(backup_path, db_path)
                
                # Reconnect to database
                self.db.connect()
            
            logger.info(f"Database restored from {backup_path}")
            return True
        except Exception as e:
            logger.error(f"Error restoring database: {e}", exc_info=True)
            return False
    
    def export_user_data(self, user_id, export_format='json'):
        """
        Export all data for a specific user.
        
        Args:
            user_id (int): Telegram user ID
            export_format (str, optional): Export format ('json' or 'csv')
            
        Returns:
            str: Path to the export file or None if failed
        """
        try:
            # Get user data
            user_data = self._get_user_data(user_id)
            
            # Create export filename with timestamp
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            export_filename = f"user_{user_id}_data_{timestamp}.{export_format}"
            export_path = os.path.join(self.backup_dir, export_filename)
            
            # Ensure backup directory exists
            os.makedirs(self.backup_dir, exist_ok=True)
            
            # Export data in the requested format
            if export_format == 'json':
                with open(export_path, 'w') as f:
                    json.dump(user_data, f, indent=2, default=str)
            elif export_format == 'csv':
                self._export_to_csv(user_data, export_path)
            else:
                logger.error(f"Unsupported export format: {export_format}")
                return None
            
            logger.info(f"User data exported to {export_path}")
            return export_path
        except Exception as e:
            logger.error(f"Error exporting user data: {e}", exc_info=True)
            return None
    
    def _get_user_data(self, user_id):
        """
        Get all data for a specific user.
        
        Args:
            user_id (int): Telegram user ID
            
        Returns:
            dict: User data
        """
        # Get user info
        self.db.cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
        user = self.db.cursor.fetchone()
        
        if not user:
            return {'user_id': user_id, 'reminders': []}
        
        user_dict = dict(user)
        
        # Get all reminders for the user
        self.db.cursor.execute('SELECT * FROM reminders WHERE user_id = ?', (user_id,))
        reminders = [dict(row) for row in self.db.cursor.fetchall()]
        
        # Combine data
        return {
            'user': user_dict,
            'reminders': reminders
        }
    
    def _export_to_csv(self, user_data, export_path):
        """
        Export user data to CSV format.
        
        Args:
            user_data (dict): User data
            export_path (str): Path to the export file
        """
        import csv
        
        # Export user info
        user_csv_path = export_path.replace('.csv', '_user.csv')
        with open(user_csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            
            # Write header
            writer.writerow(user_data['user'].keys())
            
            # Write data
            writer.writerow(user_data['user'].values())
        
        # Export reminders
        reminders_csv_path = export_path.replace('.csv', '_reminders.csv')
        with open(reminders_csv_path, 'w', newline='') as f:
            if not user_data['reminders']:
                writer = csv.writer(f)
                writer.writerow(['No reminders found'])
            else:
                writer = csv.DictWriter(f, fieldnames=user_data['reminders'][0].keys())
                writer.writeheader()
                writer.writerows(user_data['reminders'])
    
    def import_user_data(self, import_path, user_id=None):
        """
        Import user data from a file.
        
        Args:
            import_path (str): Path to the import file
            user_id (int, optional): Telegram user ID to import for
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Determine file format
            if import_path.endswith('.json'):
                with open(import_path, 'r') as f:
                    user_data = json.load(f)
            elif import_path.endswith('.csv'):
                user_data = self._import_from_csv(import_path)
            else:
                logger.error(f"Unsupported import format: {import_path}")
                return False
            
            # If user_id is provided, override the one in the file
            if user_id:
                user_data['user']['user_id'] = user_id
            
            # Import user data
            self._import_user_data(user_data)
            
            logger.info(f"User data imported from {import_path}")
            return True
        except Exception as e:
            logger.error(f"Error importing user data: {e}", exc_info=True)
            return False
    
    def _import_from_csv(self, import_path):
        """
        Import user data from CSV format.
        
        Args:
            import_path (str): Path to the import file
            
        Returns:
            dict: User data
        """
        import csv
        
        # Import user info
        user_csv_path = import_path.replace('.csv', '_user.csv')
        user = {}
        with open(user_csv_path, 'r', newline='') as f:
            reader = csv.reader(f)
            headers = next(reader)
            values = next(reader)
            user = dict(zip(headers, values))
        
        # Import reminders
        reminders_csv_path = import_path.replace('.csv', '_reminders.csv')
        reminders = []
        with open(reminders_csv_path, 'r', newline='') as f:
            reader = csv.DictReader(f)
            reminders = [row for row in reader]
        
        return {
            'user': user,
            'reminders': reminders
        }
    
    def _import_user_data(self, user_data):
        """
        Import user data into the database.
        
        Args:
            user_data (dict): User data
        """
        # Import user info
        user = user_data['user']
        self.db.add_user(
            user['user_id'],
            user.get('first_name', ''),
            user.get('last_name', ''),
            user.get('username', '')
        )
        
        # Import reminders
        for reminder in user_data['reminders']:
            self.db.add_reminder(
                user_id=reminder['user_id'],
                title=reminder['title'],
                description=reminder.get('description'),
                due_date=reminder.get('due_date'),
                category=reminder.get('category'),
                priority=reminder.get('priority', 'medium'),
                is_recurring=reminder.get('is_recurring', False),
                recurrence_pattern=reminder.get('recurrence_pattern')
            )
    
    def list_backups(self):
        """
        List all available backups.
        
        Returns:
            list: List of backup files
        """
        try:
            # Get all .db files in the backup directory
            backups = [f for f in os.listdir(self.backup_dir) if f.endswith('.db')]
            
            # Sort by modification time (newest first)
            backups.sort(key=lambda x: os.path.getmtime(os.path.join(self.backup_dir, x)), reverse=True)
            
            return backups
        except Exception as e:
            logger.error(f"Error listing backups: {e}", exc_info=True)
            return []
    
    def cleanup_old_backups(self, max_backups=10):
        """
        Remove old backups, keeping only the most recent ones.
        
        Args:
            max_backups (int, optional): Maximum number of backups to keep
            
        Returns:
            int: Number of backups removed
        """
        try:
            backups = self.list_backups()
            
            # If we have more backups than the maximum, remove the oldest ones
            if len(backups) > max_backups:
                backups_to_remove = backups[max_backups:]
                
                for backup in backups_to_remove:
                    backup_path = os.path.join(self.backup_dir, backup)
                    os.remove(backup_path)
                    logger.info(f"Removed old backup: {backup_path}")
                
                return len(backups_to_remove)
            
            return 0
        except Exception as e:
            logger.error(f"Error cleaning up old backups: {e}", exc_info=True)
            return 0
