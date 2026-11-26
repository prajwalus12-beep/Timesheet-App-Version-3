"""Unit & integration tests for Two-Factor Authentication (2FA)."""
import os
import sys
import time
import ast
import unittest
import pyotp

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from services.two_factor_service import (
    generate_totp_secret,
    get_provisioning_uri,
    generate_qr_code_bytes,
    verify_totp_code,
    generate_recovery_codes,
    hash_recovery_codes,
    verify_and_consume_recovery_code,
    check_2fa_rate_limit,
    compute_next_2fa_lockout,
    MAX_2FA_ATTEMPTS,
)


class TestTwoFactorAuth(unittest.TestCase):
    def test_captcha_removed_from_login_page(self):
        with open("pages/login_page.py", "r", encoding="utf-8") as f:
            src = f.read()
        self.assertNotIn("captcha", src.lower())

    def test_totp_generation_qr_and_verification(self):
        secret = generate_totp_secret()
        self.assertTrue(len(secret) >= 16)

        uri = get_provisioning_uri(secret, "john.doe")
        self.assertTrue(uri.startswith("otpauth://totp/"))
        self.assertIn("secret=" + secret, uri)

        qr_bytes = generate_qr_code_bytes(uri)
        self.assertTrue(qr_bytes.startswith(b"\x89PNG"))

        now_ts = time.time()
        totp = pyotp.TOTP(secret, digits=6, interval=30)
        valid_code = totp.at(now_ts)

        ok, step, err = verify_totp_code(secret, valid_code, current_time=now_ts)
        self.assertTrue(ok, err)
        self.assertIsNotNone(step)

        # Replay protection: reusing the same code/step must fail
        ok_replay, _, err_replay = verify_totp_code(
            secret, valid_code, last_used_timestep=step, current_time=now_ts
        )
        self.assertFalse(ok_replay)
        self.assertIn("already been used", err_replay.lower())

        # Invalid code fails
        ok_bad, _, _ = verify_totp_code(secret, "000000" if valid_code != "000000" else "999999", current_time=now_ts)
        self.assertFalse(ok_bad)

    def test_clock_skew_tolerance(self):
        secret = generate_totp_secret()
        now_ts = time.time()
        totp = pyotp.TOTP(secret, digits=6, interval=30)
        prev_step_code = totp.at(now_ts - 30)
        ok, _, err = verify_totp_code(secret, prev_step_code, current_time=now_ts)
        self.assertTrue(ok, err)

    def test_recovery_codes_single_use(self):
        codes = generate_recovery_codes(8)
        self.assertEqual(len(codes), 8)
        hashed = hash_recovery_codes(codes)
        self.assertEqual(len(hashed), 8)
        self.assertNotEqual(codes[0], hashed[0])

        # Valid recovery code succeeds and is consumed
        ok, remaining = verify_and_consume_recovery_code(codes[0], hashed)
        self.assertTrue(ok)
        self.assertEqual(len(remaining), 7)

        # Reusing same recovery code fails
        ok2, remaining2 = verify_and_consume_recovery_code(codes[0], remaining)
        self.assertFalse(ok2)
        self.assertEqual(len(remaining2), 7)

    def test_rate_limiting_lockout(self):
        failed = 0
        locked_until = None
        for _ in range(MAX_2FA_ATTEMPTS):
            failed, locked_until = compute_next_2fa_lockout(failed)
        self.assertEqual(failed, MAX_2FA_ATTEMPTS)
        self.assertIsNotNone(locked_until)

        allowed, msg = check_2fa_rate_limit({"locked_until": locked_until})
        self.assertFalse(allowed)
        self.assertIn("locked", msg.lower())

    def test_python_syntax_all_modified_files(self):
        files = [
            "app.py",
            "components/sidebar.py",
            "services/auth_service.py",
            "services/two_factor_service.py",
            "database/queries.py",
            "pages/login_page.py",
            "pages/employee_2fa_page.py",
            "pages/admin_2fa_page.py",
            "pages/employees_page.py",
        ]
        for f in files:
            with open(f, "r", encoding="utf-8") as fh:
                ast.parse(fh.read())


if __name__ == "__main__":
    unittest.main()
