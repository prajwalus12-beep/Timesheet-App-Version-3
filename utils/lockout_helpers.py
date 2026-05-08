import json
import os

LOCKOUT_FILE_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config', 'lockout_settings.json')

def get_lockout_schedule():
    """Read the weekly lockout schedule from config file."""
    if not os.path.exists(LOCKOUT_FILE_PATH):
        # Default all days to unlocked (False)
        return {day: False for day in ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]}
    try:
        with open(LOCKOUT_FILE_PATH, 'r') as f:
            data = json.load(f)
            return data.get("lockout_schedule", {day: False for day in ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]})
    except Exception as e:
        print(f"Error reading lockout schedule: {e}")
        return {day: False for day in ["SUN", "MON", "TUE", "WED", "THU", "FRI", "SAT"]}

def save_lockout_schedule(schedule):
    """Save the weekly lockout schedule to config file."""
    try:
        # Ensure directory exists
        os.makedirs(os.path.dirname(LOCKOUT_FILE_PATH), exist_ok=True)
        with open(LOCKOUT_FILE_PATH, 'w') as f:
            json.dump({"lockout_schedule": schedule}, f, indent=4)
        return True
    except Exception as e:
        print(f"Error saving lockout schedule: {e}")
        return False
