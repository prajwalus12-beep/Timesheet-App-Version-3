import streamlit as st
import bcrypt
import re
import secrets
import string
from cryptography.fernet import Fernet
from datetime import datetime, timedelta

FIXED_PASSWORD = "NyT@i9Us!Q7kLm2Z"

def get_fernet():
    """Returns a Fernet instance using the key from secrets."""
    try:
        key = st.secrets["postgres"]["encryption_key"].encode()
        return Fernet(key)
    except Exception as e:
        st.error(f"Encryption error: Missing or invalid encryption key. {e}")
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
        uid, emp_id, uname, db_pw, failed, locked_until = user_record
        if locked_until and datetime.now() < locked_until:
            wait = int((locked_until - datetime.now()).total_seconds() / 60) + 1
            return {"error": f"Account locked. Try in {wait} min."}
        
        if verify_password(password, db_pw):
            if failed > 0: update_user_lockout(username, 0, None)
            # Removed automatic re-hashing to preserve admin visibility
            return {"id": uid, "employee_id": emp_id, "username": uname, 
                    "role": "admin" if uname in ["admin", "System Administrator"] else "employee"}
        else:
            new_failed = failed + 1
            lockout = datetime.now() + timedelta(minutes=15) if new_failed >= 5 else None
            update_user_lockout(username, new_failed, lockout)
            if lockout: return {"error": "Too many failed attempts. Locked for 15 min."}
            return {"error": f"Invalid password. Attempt {new_failed}/5."}
    return {"error": "User not found."}

def logout_user():
    for key in list(st.session_state.keys()): del st.session_state[key]
    st.rerun()

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state["logged_in"] = False
        st.session_state["user"] = None
    return st.session_state["user"]
