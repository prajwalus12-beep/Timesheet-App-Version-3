"""
Two-Factor Authentication (2FA) Service — RFC 6238 TOTP
=========================================================
Provides standard TOTP generation, QR code creation, backend code verification
with clock-skew tolerance and replay protection, single-use recovery codes,
Fernet encryption at rest, and rate-limit helpers.
"""

import io
import time
import hashlib
import secrets
import string
from datetime import datetime, timedelta, timezone
import pyotp
import qrcode
from services.auth_service import encrypt_data, decrypt_data

TOTP_ISSUER = "FMP Timesheet Portal"
TOTP_DIGITS = 6
TOTP_INTERVAL = 30
TOTP_VALID_WINDOW = 1  # ±1 time step (±30s clock-skew tolerance)
MAX_2FA_ATTEMPTS = 5
LOCKOUT_2FA_MINUTES = 15


def generate_totp_secret() -> str:
    """Generate a unique 160-bit Base32 TOTP secret (RFC 6238 compatible)."""
    return pyotp.random_base32()


def get_provisioning_uri(secret: str, username: str, issuer: str = TOTP_ISSUER) -> str:
    """Build standard otpauth:// URI compatible with Google/Microsoft Authenticator, Authy, etc."""
    totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)
    return totp.provisioning_uri(name=username, issuer_name=issuer)


def generate_qr_code_bytes(uri: str) -> bytes:
    """Render an otpauth:// URI as PNG image bytes for display in Streamlit."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=8,
        border=3,
    )
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0F172A", back_color="#FFFFFF")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def verify_totp_code(
    secret: str,
    code: str,
    last_used_timestep: int = None,
    current_time: float = None,
) -> tuple[bool, int | None, str]:
    """
    Verify a 6-digit TOTP code with ±1 window tolerance and replay protection.

    Returns:
        (is_valid, matched_timestep, error_message)
    """
    if not secret or not code:
        return False, None, "Verification code is required."

    clean_code = str(code).strip().replace(" ", "")
    if not clean_code.isdigit() or len(clean_code) != TOTP_DIGITS:
        return False, None, "Please enter a valid 6-digit numeric code."

    now_ts = current_time if current_time is not None else time.time()
    current_step = int(now_ts // TOTP_INTERVAL)
    totp = pyotp.TOTP(secret, digits=TOTP_DIGITS, interval=TOTP_INTERVAL)

    for offset in range(-TOTP_VALID_WINDOW, TOTP_VALID_WINDOW + 1):
        candidate_step = current_step + offset
        expected_code = totp.at(candidate_step * TOTP_INTERVAL)
        if secrets.compare_digest(clean_code, expected_code):
            # Prevent reuse of the same or older accepted TOTP code
            if last_used_timestep is not None and candidate_step <= int(last_used_timestep):
                return (
                    False,
                    None,
                    "This code has already been used. Please wait for the next 30-second code.",
                )
            return True, candidate_step, ""

    return False, None, "Invalid 6-digit authenticator code. Please try again."


def encrypt_totp_secret(secret: str) -> str:
    """Encrypt TOTP secret for storage at rest using Fernet."""
    return encrypt_data(secret)


def decrypt_totp_secret(encrypted_secret: str) -> str:
    """Decrypt TOTP secret for backend verification only."""
    return decrypt_data(encrypted_secret)


def generate_recovery_codes(count: int = 8) -> list[str]:
    """Generate single-use backup recovery codes in XXXX-XXXX format."""
    alphabet = string.ascii_uppercase + string.digits
    # Exclude ambiguous characters (0, O, 1, I)
    alphabet = "".join(c for c in alphabet if c not in "0O1I")
    codes = []
    for _ in range(count):
        part1 = "".join(secrets.choice(alphabet) for _ in range(4))
        part2 = "".join(secrets.choice(alphabet) for _ in range(4))
        codes.append(f"{part1}-{part2}")
    return codes


def hash_recovery_code(code: str) -> str:
    """Normalize and SHA-256 hash a recovery code for secure storage."""
    normalized = str(code).strip().upper().replace("-", "").replace(" ", "")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def hash_recovery_codes(codes: list[str]) -> list[str]:
    """Hash a list of recovery codes."""
    return [hash_recovery_code(c) for c in codes]


def verify_and_consume_recovery_code(code: str, hashed_codes: list[str]) -> tuple[bool, list[str]]:
    """
    Verify a recovery code against stored hashes and consume it (single-use).

    Returns:
        (is_valid, remaining_hashed_codes)
    """
    if not code or not hashed_codes:
        return False, hashed_codes or []

    candidate_hash = hash_recovery_code(code)
    for idx, stored_hash in enumerate(hashed_codes):
        if secrets.compare_digest(candidate_hash, stored_hash):
            remaining = hashed_codes[:idx] + hashed_codes[idx + 1 :]
            return True, remaining
    return False, hashed_codes


def check_2fa_rate_limit(record: dict) -> tuple[bool, str]:
    """
    Check if a user is currently rate-limited for 2FA verification.

    Returns:
        (is_allowed, error_message)
    """
    if not record:
        return True, ""

    locked_until = record.get("locked_until")
    if not locked_until:
        return True, ""

    now = datetime.now(timezone.utc)
    if isinstance(locked_until, str):
        try:
            locked_dt = datetime.fromisoformat(locked_until)
            if locked_dt.tzinfo is None:
                locked_dt = locked_dt.replace(tzinfo=timezone.utc)
        except Exception:
            return True, ""
    else:
        locked_dt = locked_until

    if now < locked_dt:
        wait_mins = int((locked_dt - now).total_seconds() / 60) + 1
        return False, f"Too many invalid 2FA attempts. Locked for {wait_mins} minute(s)."

    return True, ""


def compute_next_2fa_lockout(current_failed: int) -> tuple[int, str | None]:
    """Increment failed 2FA attempts and compute lockout timestamp if threshold reached."""
    new_failed = (current_failed or 0) + 1
    if new_failed >= MAX_2FA_ATTEMPTS:
        locked_until = (datetime.now(timezone.utc) + timedelta(minutes=LOCKOUT_2FA_MINUTES)).isoformat()
        return new_failed, locked_until
    return new_failed, None
