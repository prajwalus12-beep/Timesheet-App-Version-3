# Admin Guide 1 — Getting Started

> [!IMPORTANT]
> This guide is for **Admin users only**. Admins have full access to all modules including employee management, settings, imports, and reports.

---

## 1. Logging In

### Navigation
Open the application URL in your browser. You will see the **Login Page**.

### Step-by-Step Login

1. **Select your username** from the dropdown list.
   - Usernames are auto-generated from your name (e.g., `john.doe`).
   - The dropdown only shows active accounts.

2. **Enter your password** in the password field.

3. Click **Sign In**.

4. **Complete Two-Factor Authentication (if enabled):**
   - If Admin 2FA is enabled for your account, you are redirected to the **Admin 2FA Verification** page.
   - Open your authenticator app (Google Authenticator, Microsoft Authenticator, Authy, or any TOTP app) and enter the **6-digit code** (or a single-use **Recovery Code**).
   - You cannot access the Admin Dashboard until 2FA verification succeeds.

### What Happens After Login
- You are redirected to the **Dashboard / Timesheet** page.
- The sidebar shows all admin modules.
- Your session remains active until you close the browser or log out.

---

## 2. Failed Login Attempts & Account Lockout

| Attempts | Result |
|----------|--------|
| 1–4 failed | Warning shown, try again |
| 5 failed | Account locked for **15 minutes** |

> [!WARNING]
> After 5 failed login attempts, your account is locked for 15 minutes. You **cannot** unlock it yourself. Wait 15 minutes or contact another admin.

---

## 3. Admin Navigation Sidebar

After login, the sidebar displays the following modules (admin view):

| Module | Description |
|--------|-------------|
| 🗒️ Timesheet | View and manage all employee timesheets |
| 📁 Projects | View project master list |
| 🔄 Project Updates | Editable project status grid |
| ➕ Add Project | Staging area for new projects |
| 👥 Employees | Add, edit, search employees |
| 📊 Reports | Analytics, KPIs, PDF export |
| 📥 Import Data | Bulk import via Excel |
| ⚙️ Settings | System settings (lockout, reminders, holidays) |
| 🔐 2FA Security | Configure Admin 2FA (QR code, manual key, recovery codes, enable/disable) |
| ❓ Help | Interactive Help & Documentation Center |

> [!NOTE]
> Employee accounts may see fewer modules depending on their permissions. Admins always see all modules.

---

## 4. Changing Your Password

### How to Change Password

1. Click your **username or profile area** in the sidebar (bottom of the sidebar).
2. A popover appears with a **"Change Password"** option.
3. Click it. A dialog box opens.
4. Fill in:
   - **Current Password** — your existing password
   - **New Password** — your desired new password
   - **Confirm New Password** — retype the new password

5. Click **Save**.

### Password Requirements

Your new password must meet **all** of the following:

| Requirement | Rule |
|-------------|------|
| Minimum length | At least **8 characters** |
| Uppercase letter | At least **1** uppercase letter (A–Z) |
| Lowercase letter | At least **1** lowercase letter (a–z) |
| Number | At least **1** digit (0–9) |
| Special character | At least **1** special character (e.g., `!@#$%^&*`) |

### Password Change Errors

| Error Message | Cause | Fix |
|---------------|-------|-----|
| "Current password is incorrect" | Wrong current password entered | Re-enter your actual current password |
| "Passwords do not match" | New and confirm passwords differ | Retype both new password fields to match |
| "Password must be at least 8 characters" | New password too short | Use 8 or more characters |
| "Password must contain uppercase, lowercase, digit, and special character" | Missing required character types | Add all required character types |
| "All fields are required" | Left a field blank | Fill all 3 fields |

---

## 5. Logging Out

Currently, closing the browser tab ends your session. There is no explicit logout button — your session does not persist across browser restarts.

---

## 6. Session Behavior

- Sessions are **browser-tab based**.
- Refreshing the page keeps you logged in.
- Opening a new tab opens a fresh login page (you must log in again in that tab).
- Admins do **not** have a weekly timesheet lock applied to them (see Settings → Lockout Schedule).

---

## Next Steps

- [Manage Employees →](./02-employee-management.md)
- [View Projects →](./03-project-management.md)
- [Import Data →](./07-data-import-export.md)
- [Configure Settings →](./08-system-settings.md)
