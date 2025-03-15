# ReminderBot

A structured, keyword-based reminder and productivity assistant for Telegram that uses inline buttons instead of free-text NLP.

## Features

- **Structured Reminder System**: Create, manage, and track reminders with predefined commands and inline buttons
- **Category Management**: Organize reminders by categories (Work, Personal, Fitness, etc.)
- **Priority Levels**: Set different priority levels for your reminders
- **Recurring Reminders**: Schedule tasks to repeat daily, weekly, or with custom patterns
- **Flash List**: Quick overview of all active tasks with a single command
- **Data Backup**: Export and import your reminder data
- **Privacy-First**: All data remains private and is stored locally

## Requirements

- Python 3.8 or higher
- Telegram account
- Telegram Bot Token (obtained from BotFather)

## Installation on Mac

### 1. Clone the Repository

```bash
git clone https://github.com/yourusername/ReminderBot.git
cd ReminderBot
```

### 2. Set Up Python Environment

```bash
# Create a virtual environment
python3 -m venv venv

# Activate the virtual environment
source venv/bin/activate

# Install required packages
pip install -r requirements.txt
```

### 3. Configure the Bot

1. Create a new bot on Telegram:
   - Open Telegram and search for `@BotFather`
   - Send the command `/newbot` and follow the instructions
   - Copy the API token provided by BotFather

2. Create a `.env` file in the project root:
   ```
   BOT_TOKEN=your_telegram_bot_token_here
   ```

### 4. Run the Bot

```bash
# Make sure your virtual environment is activated
source venv/bin/activate

# Run the bot
python main.py
```

## VS Code Integration

### 1. Install VS Code

If you don't have VS Code installed, download it from [code.visualstudio.com](https://code.visualstudio.com/).

### 2. Install Python Extension

1. Open VS Code
2. Go to Extensions (Ctrl+Shift+X or Cmd+Shift+X)
3. Search for "Python"
4. Install the Python extension by Microsoft

### 3. Open the Project in VS Code

```bash
# Navigate to the project directory
cd /path/to/ReminderBot

# Open VS Code
code .
```

### 4. Configure Python Interpreter

1. Press `Cmd+Shift+P` to open the Command Palette
2. Type "Python: Select Interpreter"
3. Select the virtual environment you created (`./venv/bin/python`)

### 5. Set Up Debugging

1. Click on the Run and Debug icon in the sidebar (or press `Cmd+Shift+D`)
2. Click "create a launch.json file"
3. Select "Python"
4. Select "Python File"
5. Replace the content of the launch.json file with:

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Run ReminderBot",
            "type": "python",
            "request": "launch",
            "program": "${workspaceFolder}/main.py",
            "console": "integratedTerminal",
            "justMyCode": true
        }
    ]
}
```

### 6. Run and Debug

- Press F5 to start the bot with debugging
- Use the Debug Console to view output and errors
- Set breakpoints by clicking in the gutter next to line numbers

## Bot Usage Instructions

### Starting the Bot

1. Search for your bot on Telegram (by the username you gave it)
2. Start a conversation with the bot by clicking "Start" or sending `/start`

### Available Commands

- `/start` - Initialize the bot and see the welcome message
- `/help` - Display help information and available commands
- `/add_reminder` - Start the process of adding a new reminder
- `/list_reminders` - Show all your active reminders
- `/delete_reminder` - Delete a specific reminder
- `/flashlist` - Quick overview of all your active tasks

### Adding a Reminder

1. Send `/add_reminder` command
2. Follow the step-by-step process:
   - Enter reminder title
   - (Optional) Add description
   - Select category from inline buttons
   - Set priority level
   - Set due date and time
   - Choose if it's recurring
   - For recurring reminders, select the pattern

### Managing Reminders

When viewing reminders, you'll see inline buttons for actions:
- Change Priority
- Postpone
- Mark Complete
- Delete

### Categories

Default categories include:
- Work
- Personal
- Health
- Shopping
- Finance
- Other

### Priority Levels

- High
- Medium
- Low

## Troubleshooting

### Bot Not Responding

1. Check if the bot is running in your terminal
2. Verify your internet connection
3. Ensure your BOT_TOKEN is correct in the .env file

### Database Issues

If you encounter database errors:
1. Stop the bot
2. Make a backup of the `data` directory
3. Delete the database file and restart the bot

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
# Reminder
