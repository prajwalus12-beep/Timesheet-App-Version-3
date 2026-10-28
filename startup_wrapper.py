"""
SSL patch wrapper - must run before anything else.
This ensures SSL verification is disabled for all HTTPS connections.
"""

import os
import ssl
import sys

# === CRITICAL: SSL patches MUST come before importing ANYTHING else ===

# Set environment variables FIRST
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''

# Patch ssl module globally BEFORE importing anything else
ssl._create_default_https_context = ssl._create_unverified_context

# Now that SSL is patched, we can run the app
import streamlit.web.cli as stcli

if __name__ == '__main__':
    sys.argv = ["streamlit", "run", "app.py"]
    stcli.main()
