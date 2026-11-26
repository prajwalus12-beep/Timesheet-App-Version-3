# Employee Guide 6 — Profile & Security

---

## Overview

This guide explains how to change your password, understand your session, and what to do if you get locked out.

---

## 1. Changing Your Password

### How to Access the Password Change Form

1. Look at the **bottom of the left sidebar**.
2. Click your **username** or the profile area.
3. A small popover (floating menu) appears.
4. Click **"Change Password"**.
5. A dialog box opens.

### How to Change Your Password

Fill in all three fields:

| Field | Description |
|-------|-------------|
| **Current Password** | Your existing password |
| **New Password** | The password you want to use |
| **Confirm New Password** | Type the new password again to confirm |

Then click **Save**.

---

## 2. Password Requirements

Your new password must meet **all** of the following rules:

| Rule | Requirement |
|------|-------------|
| Length | At least **8 characters** |
| Uppercase | At least **1 uppercase letter** (A–Z) |
| Lowercase | At least **1 lowercase letter** (a–z) |
| Number | At least **1 digit** (0–9) |
| Special character | At least **1 special character** (e.g., `! @ # \$ % ^ & *`) |

### Good Password Examples

✅ `MyWork@2024`  
✅ `Secure#Pass1`  
✅ `Timesheet!99`

### Bad Password Examples

❌ `password` — no uppercase, no number, no special char  
❌ `Password1` — no special character  
❌ `abc` — too short  

---

## 3. Password Change Errors

| Error Message | Cause | Fix |
|---------------|-------|-----|
| "Current password is incorrect" | Wrong current password entered | Re-enter your actual current password |
| "Passwords do not match" | New and confirm fields don't match | Retype both new password fields carefully |
| "Password must be at least 8 characters" | New password is too short | Use 8 or more characters |
| "Password must contain uppercase, lowercase, digit, and special character" | Missing required character types | Add all required types to your password |
| "All fields are required" | Left a field blank | Fill all 3 fields before saving |

---

## 4. After Changing Your Password

- The dialog closes automatically on success.
- A success message appears briefly.
- Use your **new password** the next time you log in.
- If you forgot to note your new password, repeat the change process to set a new one.

---

## 5. What to Do If You Are Locked Out

If you enter your password incorrectly 5 times in a row:

- Your account is **locked for 15 minutes**.
- You will see a message on the login page indicating the lockout.
- **Wait 15 minutes** and try again.
- If you don't remember your password after the lockout clears, contact your admin and ask them to reset your password.

> [!WARNING]
> You cannot unlock your own account. Only time (15 minutes) or an admin password reset can restore access.

---

## 6. What to Do If You Forget Your Password

You cannot reset your password from the login page (there is no "Forgot Password" link).

**Steps:**
1. Contact your admin.
2. Ask them to reset your password from the Employee Management module.
3. Log in with the new temporary password your admin provides.
4. Immediately change it using the in-app Change Password feature described above.

---

## 7. Session Security

| Situation | What Happens |
|-----------|--------------|
| Browser tab closed | Session ends |
| Page refreshed | Stay logged in |
| New browser tab opened | Must log in again |
| Shared computer | Always close the tab after use |

> [!CAUTION]
> If you use a shared or public computer, **always close the browser tab** (or the entire browser) after finishing your work. Otherwise, the next person to open the browser may access your account.

---

## 8. Your Username

Your username is automatically generated from your name when your admin creates your account.

Format: `firstname.lastname` (e.g., `john.doe`)

- You **cannot change your username**.
- If your name changes (e.g., due to marriage), contact your admin to update your profile information. The username will remain the same.

---

## 9. Two-Factor Authentication (2FA)

Two-Factor Authentication adds a second layer of security to your login using any standard TOTP authenticator app (**Google Authenticator**, **Microsoft Authenticator**, **Authy**, etc.).

### How to Enable & Configure 2FA

1. Open **🔐 2FA Security** in the sidebar (or you will be prompted automatically at login if your Admin enabled 2FA for your account).
2. Open your authenticator app and tap **+ / Add Account**.
3. **Scan the QR code** on screen, **or** copy and enter the **Manual Setup Key**.
4. Enter the **6-digit verification code** shown in your authenticator app and click **Verify & Enable 2FA**.
5. **Save your 8 single-use Recovery Codes** (`XXXX-XXXX` format) in a safe place (download or copy them). Each recovery code can be used once if you lose your phone.

### How to Disable Your Own 2FA

1. Go to **🔐 2FA Security** in the sidebar.
2. Click **Disable My 2FA**.
3. You can re-enable 2FA at any time.

> [!NOTE]
> After 5 failed 2FA verification attempts, verification is locked for **15 minutes** for security.
