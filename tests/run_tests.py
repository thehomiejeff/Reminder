"""
Test script for running the ReminderBot.
This script runs the tests and verifies the functionality.
"""
import os
import sys
import unittest

# Add the parent directory to the path so we can import the tests package
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tests.test_reminderbot import TestReminderBot

if __name__ == '__main__':
    # Create data directories if they don't exist
    os.makedirs('data', exist_ok=True)
    os.makedirs('data/test_backups', exist_ok=True)
    
    # Run the tests
    unittest.main(module=TestReminderBot)
