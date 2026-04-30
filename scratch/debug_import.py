import sys
import os

# Ensure we can import from database module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from database.queries import import_project_updates

print("Debugging import_project_updates")

# Let's create a dummy excel file and test import
df = pd.DataFrame([["P001", "High", "Website Redesign", "In progress", "Alice", "https://trello.com/b/123", "2025-01-01", "2025-06-30"]],
                  columns=['Job No', 'Job Priority', 'Project', 'Status', 'Lead engineer', 'Trello', 'Start Date', 'End Date'])
result = import_project_updates(df)
print(f"Result: {result}")
