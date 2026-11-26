# Admin Guide 9 — Troubleshooting & FAQ

---

## Overview

This guide covers the most common issues admins encounter, their causes, and step-by-step solutions.

---

## 🔐 Login & Access Issues

### Q: An employee is locked out. What do I do?

**Cause:** The employee entered the wrong password 5 times.

**Solution:**
1. Wait 15 minutes for the lockout to expire automatically.
2. Alternatively, reset their password in **Employees → Edit Employee**.
3. Have them log in with the new password.

---

### Q: An employee says they cannot log in and the lockout timer hasn't expired.

**Possible causes:**
- Their account status is set to **Inactive**.
- Their username was typed incorrectly.

**Solution:**
1. Go to **Employees → Directory** and search for the employee.
2. Check their **Status** column — it must say `Active`.
3. If it says `Inactive`, go to **Edit Employee** and change to `Active`.

---

### Q: An employee lost their authenticator app or is locked out of 2FA.

**Solution:**
1. The employee can sign in using one of their single-use **Recovery Codes** (`XXXX-XXXX`) on the **Recovery Code** tab of the 2FA Verification screen.
2. If they lost all recovery codes or are locked out (5 failed 2FA attempts = 15-minute lock), go to **Employees → 🔐 2FA Management** and click **Disable 2FA** (or re-enable 2FA so they can re-configure a new QR code on next login).

---

## 📥 Import Issues

### Q: Import Update Projects shows "0 new entries" but I uploaded new data.

**Most likely cause:** All project codes in your file already exist in the database from a previous import.

**How to verify:**
- The import summary shows `X updated, 0 new`. If records were updated, the import worked correctly.
- If `X updated = 0` as well, it means the data in your file exactly matches what's already in the database.

**What to do:**
- If you expected new project codes, verify the **Job No** column in your file contains codes that don't yet exist in the system.
- Use **Import Projects** first to add master records before updating them.

---

### Q: Import Update Projects shows "X skipped (FK not found)".

**Cause:** Some project codes in the update file don't exist in the master project table.

**Solution:**
1. Run **Import Projects** first with the same project codes.
2. Then re-run **Import Update Projects**.

---

### Q: I see the warning "Workbook contains no default style".

**Cause:** The Excel file has a minor formatting difference from the openpyxl default.

**Is it a problem?** No. This is a harmless warning. Your data imports correctly. You can safely ignore it.

---

### Q: Import fails with "Invalid column" error.

**Cause:** Your Excel file uses different column names than expected.

**Solution:**
1. Click **"Download Sample"** in the import section.
2. Use the sample as your template.
3. Copy your data into the sample file, keeping column names exactly as shown.

---

## 📊 Reports Issues

### Q: Reports show no data.

**Cause options:**
- The date range filter excludes the period you're looking at.
- No employees are selected in the Employee filter.
- No timesheet entries exist for the selected period.

**Solution:**
1. Clear all filters (set Date Range to a wide period).
2. Remove any Employee or Project filter.
3. If still empty, check if employees have submitted timesheets for that period.

---

## ⚙️ Settings Issues

### Q: Reminder emails are not being received by employees.

**Checklist:**
1. Verify SMTP credentials in **Settings → Reminder Settings**.
2. Check that the SMTP port is correct (`587` for TLS, `465` for SSL).
3. Ensure the sender email account has SMTP access enabled (for Gmail, use an App Password).
4. Verify employees have valid email addresses in their profiles.
5. Check if the reminder schedule is configured for the current day and time.

---

### Q: An employee says they can't edit Project Updates.

**Cause:** The employee doesn't have `project_update_access` permission.

**Solution:**
1. Go to **Settings → Employee Permissions**.
2. Find the employee.
3. Toggle **project_update_access** to ON.
4. Have the employee refresh their browser.

---

### Q: Weekly lockout is blocking employees on the wrong days.

**Solution:**
1. Go to **Settings → Lockout Schedule**.
2. Review the OPEN/BLOCKED toggles.
3. Set the correct days to OPEN.
4. Changes take effect immediately — no restart required.

---

## 🗒️ Timesheet Issues

### Q: An employee's timesheet entry is missing.

**Possible causes:**
- The entry was deleted.
- The date filter is hiding it.
- The employee submitted it under a different project.

**Solution:**
1. In Timesheet Administration, set the Employee filter to that employee.
2. Set Date Range to **Custom Range** covering the missing date.
3. Remove the Project filter to see all projects.
4. If still not found, the entry may not have been saved. Ask the employee to re-submit.

---

### Q: An employee cannot add a timesheet entry.

**Possible causes:**
- The day is set to **BLOCKED** in the Lockout Schedule.
- The employee is trying to submit for a week that is locked.

**Solution:**
1. Check **Settings → Lockout Schedule** for the current day.
2. If blocked, either change the schedule or manually add the entry on behalf of the employee using the admin Timesheet view.

---

## 📂 Project Issues

### Q: A project is not showing up in the timesheet project dropdown.

**Cause:** The project may not be imported yet, or its status is Inactive/Cancelled.

**Solution:**
1. Check **Projects** page — search for the project code.
2. If not found, run **Import → Import Projects**.
3. If found but not appearing in dropdowns, check the project's status.

---

## Still Need Help?

If your issue is not covered above:
1. Check the specific module documentation linked from [README.md](../README.md).
2. Contact your application development team with:
   - The exact error message
   - Which module you were in
   - What action you were performing
   - Your username and the time of the error
