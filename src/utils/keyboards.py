"""
Main keyboard utilities for ReminderBot.
Provides functions for creating inline keyboards and reply keyboards.
"""
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup
from src.config import REMINDER_CATEGORIES, RECURRING_OPTIONS, PRIORITY_LEVELS

def get_main_menu_keyboard():
    """
    Get the main menu inline keyboard.
    
    Returns:
        InlineKeyboardMarkup: Main menu keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton("📌 Add Reminder", callback_data="add_reminder"),
            InlineKeyboardButton("📋 View Reminders", callback_data="list_reminders")
        ],
        [
            InlineKeyboardButton("❌ Delete Reminder", callback_data="delete_reminder"),
            InlineKeyboardButton("🔄 Recurring Tasks", callback_data="recurring_tasks")
        ],
        [
            InlineKeyboardButton("⚡ Quick View", callback_data="flashlist"),
            InlineKeyboardButton("⚙️ Settings", callback_data="settings")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_categories_keyboard():
    """
    Get the categories selection inline keyboard.
    
    Returns:
        InlineKeyboardMarkup: Categories keyboard
    """
    # Create buttons in rows of 2
    keyboard = []
    row = []
    
    for i, category in enumerate(REMINDER_CATEGORIES):
        row.append(InlineKeyboardButton(category, callback_data=f"category_{category}"))
        
        # Create a new row after every 2 buttons
        if (i + 1) % 2 == 0 or i == len(REMINDER_CATEGORIES) - 1:
            keyboard.append(row)
            row = []
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_priority_keyboard():
    """
    Get the priority selection inline keyboard.
    
    Returns:
        InlineKeyboardMarkup: Priority keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton(f"{PRIORITY_LEVELS['high']}", callback_data="priority_high"),
            InlineKeyboardButton(f"{PRIORITY_LEVELS['medium']}", callback_data="priority_medium"),
            InlineKeyboardButton(f"{PRIORITY_LEVELS['low']}", callback_data="priority_low")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_recurring_options_keyboard():
    """
    Get the recurring options inline keyboard.
    
    Returns:
        InlineKeyboardMarkup: Recurring options keyboard
    """
    keyboard = []
    
    # Add recurring options
    for key, value in RECURRING_OPTIONS.items():
        keyboard.append([InlineKeyboardButton(value, callback_data=f"recurring_{key}")])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_yes_no_keyboard(callback_prefix):
    """
    Get a simple Yes/No inline keyboard.
    
    Args:
        callback_prefix (str): Prefix for callback data
    
    Returns:
        InlineKeyboardMarkup: Yes/No keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton("✅ Yes", callback_data=f"{callback_prefix}_yes"),
            InlineKeyboardButton("❌ No", callback_data=f"{callback_prefix}_no")
        ]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_reminders_list_keyboard(reminders):
    """
    Get a keyboard with reminder list for selection.
    
    Args:
        reminders (list): List of reminder objects
    
    Returns:
        InlineKeyboardMarkup: Reminders list keyboard
    """
    keyboard = []
    
    # Add buttons for each reminder
    for reminder in reminders:
        # Truncate title if too long
        title = reminder.title if len(reminder.title) <= 30 else reminder.title[:27] + "..."
        # Add priority emoji
        title = f"{reminder.get_priority_emoji()} {title}"
        keyboard.append([InlineKeyboardButton(title, callback_data=f"reminder_{reminder.id}")])
    
    # Add back button
    keyboard.append([InlineKeyboardButton("⬅️ Back", callback_data="back_to_main")])
    
    return InlineKeyboardMarkup(keyboard)

def get_reminder_actions_keyboard(reminder_id):
    """
    Get a keyboard with actions for a specific reminder.
    
    Args:
        reminder_id (int): Reminder ID
    
    Returns:
        InlineKeyboardMarkup: Reminder actions keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton("⏫ Change Priority", callback_data=f"change_priority_{reminder_id}"),
            InlineKeyboardButton("⏳ Postpone", callback_data=f"postpone_{reminder_id}")
        ],
        [
            InlineKeyboardButton("✔️ Mark Complete", callback_data=f"complete_{reminder_id}"),
            InlineKeyboardButton("❌ Delete", callback_data=f"confirm_delete_{reminder_id}")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data="back_to_list")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_postpone_options_keyboard(reminder_id):
    """
    Get a keyboard with postpone options.
    
    Args:
        reminder_id (int): Reminder ID
    
    Returns:
        InlineKeyboardMarkup: Postpone options keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton("1 Hour", callback_data=f"postpone_{reminder_id}_1h"),
            InlineKeyboardButton("3 Hours", callback_data=f"postpone_{reminder_id}_3h")
        ],
        [
            InlineKeyboardButton("1 Day", callback_data=f"postpone_{reminder_id}_1d"),
            InlineKeyboardButton("1 Week", callback_data=f"postpone_{reminder_id}_1w")
        ],
        [InlineKeyboardButton("⬅️ Back", callback_data=f"reminder_{reminder_id}")]
    ]
    return InlineKeyboardMarkup(keyboard)

def get_settings_keyboard():
    """
    Get the settings menu inline keyboard.
    
    Returns:
        InlineKeyboardMarkup: Settings keyboard
    """
    keyboard = [
        [
            InlineKeyboardButton("🕒 Set Timezone", callback_data="set_timezone"),
            InlineKeyboardButton("🔔 Notifications", callback_data="notifications")
        ],
        [InlineKeyboardButton("⬅️ Back to Main Menu", callback_data="back_to_main")]
    ]
    return InlineKeyboardMarkup(keyboard)
