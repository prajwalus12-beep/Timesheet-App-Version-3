import sys
import os

# Ensure we can import from database module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import pandas as pd
from database.connection import get_supabase_client

supabase = get_supabase_client()
res = supabase.table('project_reports').select('project_code, start_date, end_date').eq('project_code', 'P001').execute()
print(f"Database query result for P001: {res.data}")
