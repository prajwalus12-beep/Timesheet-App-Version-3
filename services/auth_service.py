import streamlit as st
import bcrypt
import re
import json
import secrets
import string
from cryptography.fernet import Fernet
from datetime import datetime, timedelta, timezone

FIXED_PASSWORD = "NyT@i9Us!Q7kLm2Z"

def get_fernet():
    """Returns a Fernet instance using the key from secrets."""
    try:
        postgres_secrets = st.secrets.get("postgres", {})
        key = postgres_secrets.get("encryption_key")
        if not key:
            st.error("""
            **Encryption key missing!**
            
            This key is required for security. Please add it to your **Streamlit Cloud Dashboard** 
            under the `[postgres]` section in **Secrets**.
            """)
            return None
        return Fernet(key.encode())
    except Exception as e:
        st.error(f"Encryption error: {e}")
        return None

def encrypt_data(text):
    """Encrypts text using Fernet."""
    if not text: return text
    f = get_fernet()
    if f: return f.encrypt(text.encode()).decode()
    return text

def decrypt_data(encrypted_text):
    """Decrypts text using Fernet."""
    if not encrypted_text: return encrypted_text
    f = get_fernet()
    if f:
        try:
            return f.decrypt(encrypted_text.encode()).decode()
        except:
            return encrypted_text
    return encrypted_text

def hash_password(password: str) -> str:
    """Securely hash a password using bcrypt."""
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')

def verify_password(password: str, hashed_password: str) -> bool:
    """Verify a password against a bcrypt hash or encrypted string."""
    try:
        if not hashed_password: return False
        # Try bcrypt first
        if hashed_password.startswith('$2b$'):
            return bcrypt.checkpw(password.encode('utf-8'), hashed_password.encode('utf-8'))
        # Try decryption
        decrypted = decrypt_data(hashed_password)
        return password == decrypted
    except:
        return password == hashed_password

def generate_secure_password() -> str:
    """Generate a random 16-character password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
    while True:
        pw = ''.join(secrets.choice(alphabet) for i in range(16))
        if (any(c.islower() for c in pw) and any(c.isupper() for c in pw) 
            and any(c.isdigit() for c in pw) and any(c in "!@#$%^&*" for c in pw)):
            return pw

def is_password_strong(password: str) -> tuple:
    """Check if password meets complexity requirements."""
    if len(password) < 12: return False, "Password must be at least 12 characters long."
    if not re.search(r"[a-z]", password): return False, "Password must contain lowercase."
    if not re.search(r"[A-Z]", password): return False, "Password must contain uppercase."
    if not re.search(r"\d", password): return False, "Password must contain number."
    if not re.search(r"[ !@#$%^&*(),.?\":{}|<>]", password): return False, "Password must contain symbol."
    return True, ""

def login_user(username, password):
    """Authenticate with lockout enforcement."""
    from database.queries import get_user_by_username, update_user_lockout
    user_record = get_user_by_username(username)
    if user_record:
        # Tuple: (id, employee_id, username, password, failed_attempts, locked_until, access, emp_name)
        uid, emp_id, uname, db_pw, failed, locked_until, access, emp_name = user_record
        
        now = datetime.now(timezone.utc)
        
        # Convert string timestamp to datetime object if needed
        if isinstance(locked_until, str):
            try:
                if ' ' in locked_until:
                    locked_until = datetime.strptime(locked_until.split('.')[0], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
                else:
                    locked_until = datetime.fromisoformat(locked_until).replace(tzinfo=timezone.utc)
            except:
                locked_until = None
        elif locked_until and locked_until.tzinfo is None:
            locked_until = locked_until.replace(tzinfo=timezone.utc)

        if locked_until and now < locked_until:
            wait = int((locked_until - now).total_seconds() / 60) + 1
            return {"error": f"Account locked for security. Please try again in {wait} min."}
        
        if verify_password(password, db_pw):
            if failed > 0: update_user_lockout(username, 0, None)
            return {
                "id": uid, 
                "employee_id": emp_id, 
                "employee_name": emp_name,
                "username": uname, 
                "role": "admin" if uname.lower() in ["admin", "system administrator"] else "employee",
                "project_update_access": access
            }
        else:
            new_failed = failed + 1
            lockout = now + timedelta(minutes=15) if new_failed >= 5 else None
            update_user_lockout(username, new_failed, lockout)
            if lockout: return {"error": "🚫 Too many failed attempts. Your account is locked for 15 minutes."}
            return {"error": f"❌ Invalid password. Attempt {new_failed}/5."}
    return {"error": "🔍 User not found."}

def get_session_metadata():
    """Helper to extract browser metadata for session binding."""
    headers = {}
    
    # 1. Modern way (Streamlit 1.35+)
    if hasattr(st, "context"):
        try:
            headers = st.context.headers
        except Exception:
            pass

    # 2. Legacy fallback for older versions
    if not headers:
        try:
            # pyrefly: ignore [missing-import]
            from streamlit.web.server.websocket_headers import _get_websocket_headers
            headers = _get_websocket_headers()
        except (ImportError, Exception):
            pass

    if not headers:
        return {"ua": "unknown", "ip": "127.0.0.1"}

    # Extract IP robustly (handling proxies)
    ip_headers = ['X-Forwarded-For', 'X-Real-IP', 'True-Client-IP']
    ip = "127.0.0.1"
    for h in ip_headers:
        val = headers.get(h)
        if val:
            ip = val.split(',')[0].strip()
            break
            
    return {
        "ua": headers.get("User-Agent", "unknown"),
        "ip": ip
    }

def create_session_token(user_data):
    """Create an encrypted session token with expiration and device binding."""
    try:
        f = get_fernet()
        if f:
            meta = get_session_metadata()
            payload = {
                "user": user_data,
                "exp": (datetime.now(timezone.utc) + timedelta(hours=24)).timestamp(),
                "ua": meta["ua"],
                "ip": meta["ip"]
            }
            return f.encrypt(json.dumps(payload).encode()).decode()
    except Exception:
        pass
    return None

def restore_session_from_token(token):
    """Verify and decrypt a session token."""
    try:
        f = get_fernet()
        if f:
            payload = json.loads(f.decrypt(token.encode()).decode())
            
            # 1. Check expiration
            if datetime.now(timezone.utc).timestamp() > payload.get("exp", 0):
                return None
            
            # 2. Check Device Binding (User-Agent must match)
            meta = get_session_metadata()
            if payload.get("ua") != meta["ua"]:
                return None
            
            return payload.get("user")
    except Exception:
        pass
    return None

def logout_user():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.query_params.clear()
    st.rerun()

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user"] = None

    # Restore session from token on refresh
    if not st.session_state["user"]:
        token = st.query_params.get("session")
        if token:
            user_data = restore_session_from_token(token)
            if user_data:
                st.session_state["logged_in"] = True
                st.session_state["user"] = user_data
                # Clear token from URL to prevent easy copying/sharing
                st.query_params.clear()
            else:
                # Invalid/expired/tampered token — clear it
                st.query_params.clear()

    return st.session_state["user"]
