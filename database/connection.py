import os
import ssl
from contextlib import contextmanager

# === CRITICAL: SSL patches MUST come before ANY other imports ===

# Set environment variables FIRST
os.environ['PYTHONHTTPSVERIFY'] = '0'
os.environ['REQUESTS_CA_BUNDLE'] = ''
os.environ['CURL_CA_BUNDLE'] = ''

# Patch ssl module BEFORE importing anything else
ssl._create_default_https_context = ssl._create_unverified_context

# Now safe to import other modules
import streamlit as st
import urllib3

# Disable SSL verification warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# Load secrets
DB_CONFIG = st.secrets.get("postgres", {})

@st.cache_resource
def get_supabase_client():
    """Initialize and return a cached Supabase Client with SSL verification disabled."""
    try:
        from supabase import create_client
        import httpx
        
        url = DB_CONFIG.get("SUPABASE_URL")
        key = DB_CONFIG.get("SUPABASE_ANON_KEY")
        if not url or not key:
            st.error("""
            **Supabase configuration missing!**
            
            Since you (correctly) added `secrets.toml` to `.gitignore`, it is not on GitHub. 
            You must manually add your secrets to the **Streamlit Cloud Dashboard**:
            1. Go to your app settings on Streamlit Cloud.
            2. Open the **Secrets** section.
            3. Paste your `[postgres]` configuration there.
            """)
            return None
        
        # Create the Supabase client normally
        client = create_client(url, key)
        
        # Now patch its internal httpx client to disable SSL verification
        try:
            # The Supabase client has a postgrest attribute with a session (httpx.Client)
            if hasattr(client, 'postgrest') and hasattr(client.postgrest, 'session'):
                session = client.postgrest.session
                if isinstance(session, httpx.Client):
                    # Create a new transport that doesn't verify SSL
                    transport = httpx.HTTPTransport(verify=False)
                    # Replace both the sync and async transports
                    session._transport_for_url = lambda url: transport
                    session._mounts['https://'] = transport
                    session._mounts['http://'] = httpx.HTTPTransport(verify=False)
        except Exception as e:
            # If patching fails, continue anyway - the global SSL patch might still work
            print(f"Warning: Could not patch httpx transport: {e}")
        
        return client
    except ImportError:
        st.error("Supabase library not installed. Please run: pip install supabase")
        return None
    except Exception as e:
        st.error(f"Failed to connect to Supabase: {e}")
        import traceback
        st.error(traceback.format_exc())
        return None

# Placeholder functions to maintain compatibility during migration
# These will be phased out as queries.py is updated
def run_query(query, params=None, fetch_all=True):
    st.error("Direct SQL queries are deprecated. Please update this call to use Supabase SDK.")
    return None

def run_transaction(query, params=None):
    st.error("Direct SQL transactions are deprecated. Please update this call to use Supabase SDK.")
    return False, "Deprecated"

@contextmanager
def get_db_connection():
    st.error("get_db_connection is deprecated. Use get_supabase_client() instead.")
    yield None
