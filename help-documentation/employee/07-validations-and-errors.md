# Employee Guide 7 — Validations & Error Messages

---

## Overview

This guide lists every validation and error message you may encounter in the application, explains why it appears, and tells you exactly how to fix it.

---

## 🔐 Login & Authentication

| Error Message | Why It Appears | How to Fix |
|---------------|----------------|------------|
| "Incorrect password" | Wrong password entered | Re-enter your correct password |
| "Account locked. Try again in X minutes." | 5 consecutive failed login attempts | Wait the stated minutes; or ask admin to reset password |
| "Invalid 6-digit authenticator code." | Wrong or expired TOTP code entered | Check your device clock and enter the current 6-digit code from your authenticator app |
| "This code has already been used." | Same 6-digit TOTP code submitted twice | Wait up to 30 seconds for the next code to generate |
| "Too many invalid 2FA attempts. Locked for 15 minute(s)." | 5 consecutive failed 2FA attempts | Wait 15 minutes or contact your admin |
| "Invalid or already used recovery code." | Wrong or previously consumed backup code | Enter an unused `XXXX-XXXX` recovery code from your saved list |
| "Username not found" | Username not in system | Check the username dropdown — select from the list, don't type manually |

---

## 📝 Timesheet Entry Validations

### When Adding or Editing a Timesheet Entry

| Error Message | Why It Appears | How to Fix |
|---------------|----------------|------------|
| "Please select a project" | No project was chosen | Search for a project and click the radio button to select it |
| "Please select an activity" | Activity dropdown not filled | Click the Activity dropdown and choose a type |
| "Please select a date" | Date field left empty | Click the date field and pick a date |
| "Date cannot be in the future" | A future date was selected | Change the date to today or any past date |
| "Hours must be between 0.5 and 24" | Hours entered are outside the allowed range | Enter a value from `0.5` to `24` (e.g., `7.5` for 7.5 hours) |
| "Entry already exists for this project and date" | A timesheet entry for this project on this date already exists | Edit the existing entry instead of adding a duplicate |

---

## 🏖️ Leave Entry Validations

| Error Message | Why It Appears | How to Fix |
|---------------|----------------|------------|
| "Please select a leave type" | No leave type selected | Pick from: Annual / Sick / Unpaid / Other / Holiday |
| "Please select a start date" | Start date field left empty | Pick the first day of your leave |
| "Please select an end date" | End date field left empty | Pick the last day of your leave |
| "End date cannot be before start date" | End date is earlier than start date | Set end date to the same as or later than start date |
| "Reason is required" | Reason field left blank | Type a brief explanation for the leave |

---

## 🔐 Password Change Validations

| Error Message | Why It Appears | How to Fix |
|---------------|----------------|------------|
| "All fields are required" | One or more fields left blank | Fill all three: Current Password, New Password, Confirm Password |
| "Current password is incorrect" | Wrong current password entered | Enter the password you currently use to log in |
| "Passwords do not match" | New Password and Confirm Password don't match | Retype both fields carefully so they match exactly |
| "Password must be at least 8 characters" | New password is too short | Use at least 8 characters |
| "Password must contain uppercase, lowercase, digit, and special character" | Password is missing one or more required character types | Ensure your password has: 1 uppercase (A–Z), 1 lowercase (a–z), 1 digit (0–9), 1 special character (!@#\$% etc.) |

---

## 📁 Project Updates Validations (Edit Access Only)

| Situation | What Happens | What to Do |
|-----------|--------------|------------|
| Trying to edit without `project_update_access` | Grid is grayed out, clicks do nothing | Contact admin to enable edit access |
| Entering invalid status | Dropdown only shows valid options | Select from the predefined list |
| Entering text in a number field (Estimated/Actual Days) | Field reverts or shows error | Enter whole numbers only |
| URL entered without `http://` | May not function as a clickable link | Enter the full URL starting with `https://` or `http://` |

---

## ➕ Add Project Validations (If You Have Access)

| Error Message | Why It Appears | How to Fix |
|---------------|----------------|------------|
| "Project Name is required" | Name field left blank | Enter the project name |
| "Project Code already exists" | A project with the same code exists in staging | Use a different project code |
| "Project Code is required" | Code field left blank | Enter a project code |

---

## 🌐 General Application Errors

| Error / Situation | Why It Happens | What to Do |
|-------------------|----------------|------------|
| Page loads blank or shows spinner indefinitely | Network connection issue or server error | Refresh the page. If problem persists, contact your admin |
| "Unauthorized" or redirect to login | Your session expired | Log in again |
| Changes not saving | Server connection lost | Check your internet connection; try saving again; refresh and re-enter data |
| Data not updating after save | Browser cache issue | Hard refresh the page (Ctrl + F5 on Windows) |

---

## 📋 Quick Reference: Required vs Optional Fields

### Timesheet Entry

| Field | Required? |
|-------|-----------|
| Project | ✅ Required |
| Activity | ✅ Required |
| Date | ✅ Required |
| Hours | ✅ Required |
| Description | Optional |

### Leave Entry

| Field | Required? |
|-------|-----------|
| Leave Type | ✅ Required |
| Start Date | ✅ Required |
| End Date | ✅ Required |
| Reason | ✅ Required |

### Password Change

| Field | Required? |
|-------|-----------|
| Current Password | ✅ Required |
| New Password | ✅ Required |
| Confirm New Password | ✅ Required |

### Add Project (Staging)

| Field | Required? |
|-------|-----------|
| Project Name | ✅ Required |
| Project Code | ✅ Required |
| All other fields | Optional |

---

## 🆘 Still Getting an Error?

If you encounter an error not listed in this guide:

1. **Note the exact error message** shown on screen.
2. **Note which page** and action you were performing.
3. **Note your username** and the **date and time** the error occurred.
4. Contact your admin or IT support with this information.
