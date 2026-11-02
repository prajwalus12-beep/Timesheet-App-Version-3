# GitHub Actions Setup for Automated Email Reports

## Overview
This guide walks you through setting up GitHub Actions to automatically send timesheet email reports based on your configured schedule, completely independent of whether your PC is on or Streamlit is running.

## Prerequisites
- GitHub repository for this project (public or private)
- Supabase credentials (URL and API key)
- SMTP email credentials (server, port, username, password)

---

## Step 1: Push Code to GitHub

If you haven't already:

```bash
# Initialize git (if not already done)
git init

# Add GitHub remote
git remote add origin https://github.com/YOUR_USERNAME/YOUR_REPO.git

# Add all files
git add .

# Commit
git commit -m "Add automated email scheduling with GitHub Actions"

# Push to GitHub
git push -u origin main
```

---

## Step 2: Add GitHub Secrets

1. Go to your GitHub repository
2. Click **Settings** (top menu)
3. In left sidebar: **Secrets and variables** → **Actions**
4. Click **New repository secret** button

Add these secrets one by one:

### Supabase Secrets

| Secret Name | Value | Where to Find |
|------------|-------|---------------|
| `SUPABASE_URL` | Your Supabase project URL | Supabase Dashboard → Project Settings → API |
| `SUPABASE_KEY` | Your Supabase anon or service key | Supabase Dashboard → Project Settings → API |

### SMTP Secrets

| Secret Name | Example Value | Description |
|------------|---------------|-------------|
| `SMTP_SERVER` | `smtp.gmail.com` | Your email provider's SMTP server |
| `SMTP_PORT` | `587` | Usually 587 for TLS or 465 for SSL |
| `SMTP_USERNAME` | `your-email@gmail.com` | Your email username |
| `SMTP_PASSWORD` | `your-app-password` | Your email password or app-specific password |
| `SMTP_FROM_EMAIL` | `your-email@gmail.com` | The "From" email address |

**Gmail Users:**
- You need to create an [App Password](https://myaccount.google.com/apppasswords)
- Use the app password as `SMTP_PASSWORD`, not your regular Gmail password
- SMTP Server: `smtp.gmail.com`, Port: `587`

---

## Step 3: Configure Schedule

The workflow file `.github/workflows/automated-emails.yml` contains a cron schedule.

**Default:** `'0 12 * * 1'` = Every Monday at 12:00 UTC

### Adjust for Your Timezone

Edit the cron expression in `.github/workflows/automated-emails.yml`:

```yaml
on:
  schedule:
    - cron: '0 12 * * 1'  # ← Change this line
```

**Common timezone conversions:**

| Your Time | Cron Expression | Notes |
|-----------|----------------|-------|
| Monday 12:00 UTC | `'0 12 * * 1'` | Default |
| Monday 12:00 IST (UTC+5:30) | `'30 6 * * 1'` | 6:30 AM UTC = 12:00 PM IST |
| Monday 09:00 EST (UTC-5) | `'0 14 * * 1'` | 2:00 PM UTC = 9:00 AM EST |
| Monday 09:00 PST (UTC-8) | `'0 17 * * 1'` | 5:00 PM UTC = 9:00 AM PST |

**Need a different day/time?**

Use [crontab.guru](https://crontab.guru/) to create your cron expression.

Cron format: `'minute hour day month weekday'`
- Minute: 0-59
- Hour: 0-23 (UTC)
- Day: 1-31
- Month: 1-12
- Weekday: 0-6 (0 = Sunday, 1 = Monday, etc.)

Examples:
- Every Friday at 5 PM UTC: `'0 17 * * 5'`
- Every day at 8 AM UTC: `'0 8 * * *'`
- First of every month at midnight UTC: `'0 0 1 * *'`

---

## Step 4: Test the Setup

### Manual Test (Recommended First)

1. Go to your GitHub repository
2. Click **Actions** tab (top menu)
3. Click **"Automated Timesheet Email Reports"** workflow in left sidebar
4. Click **"Run workflow"** button (blue button on right)
5. Select **"weekly-report"** and click **"Run workflow"**

**Watch the execution:**
- Click on the running workflow to see real-time logs
- Check each step: Checkout → Setup Python → Install deps → Run scheduler
- Look for "Email sent successfully" in the logs

### Check for Errors

If the workflow fails:
1. Click on the failed workflow run
2. Click on the failed step to see error details
3. Common issues:
   - **Secrets not set:** Double-check all 7 secrets are added
   - **Wrong credentials:** Verify SMTP and Supabase credentials
   - **Missing dependencies:** Check `requirements.txt` includes all packages
   - **Python version:** Workflow uses Python 3.10

---

## Step 5: Verify Scheduled Runs

After your first manual test succeeds:

1. Wait for the scheduled time (based on your cron expression)
2. Go to **Actions** tab to see if workflow ran automatically
3. Check the email was received by configured recipients

**Note:** GitHub Actions may delay cron jobs by 5-15 minutes during peak usage times.

---

## Monitoring and Logs

### View Past Runs
- Go to **Actions** tab
- Click any workflow run to see logs
- Logs are kept for 90 days

### Download Logs
If your scheduler creates log files in `/logs`:
1. Go to completed workflow run
2. Scroll to **Artifacts** section at bottom
3. Download **"email-logs"** artifact
4. Logs are kept for 7 days

### Email Notifications
GitHub can notify you when workflows fail:
1. Go to repository **Settings** → **Notifications**
2. Configure email notifications for workflow failures

---

## Troubleshooting

### Workflow doesn't run at scheduled time
- GitHub Actions cron can be delayed 5-15 minutes during peak times
- Check if workflow is enabled: Actions tab → workflow → "..." menu → ensure "Enable workflow" is checked
- Verify cron expression is correct using [crontab.guru](https://crontab.guru/)

### Email not sent
- Check workflow logs in Actions tab
- Verify all 7 secrets are set correctly
- Test SMTP credentials manually
- Check Supabase connection
- Verify report settings are configured in the app (Settings page)

### "Module not found" errors
- Add missing package to `requirements.txt`
- Commit and push changes
- Re-run workflow

### Wrong date range in email
- Check your report settings in the Streamlit app (Settings → Email Report Settings)
- Verify `date_range_filter` is set correctly in database
- Manual test: Use "Send Email Report" button in Reports page

---

## Cost and Limits

### GitHub Actions Pricing
- **Public repositories:** Unlimited minutes (free)
- **Private repositories:** 2,000 minutes/month free
  - Each workflow run uses ~2-5 minutes
  - ~400-1000 runs per month for free

### Rate Limits
- GitHub Actions: No specific rate limit for cron jobs
- SMTP: Check your email provider's sending limits
  - Gmail: 500 emails/day for regular accounts
  - 2000 emails/day for Google Workspace

---

## Security Best Practices

✅ **DO:**
- Store all credentials as GitHub Secrets
- Use app-specific passwords (Gmail App Passwords)
- Rotate secrets periodically
- Use Supabase anon key (not service role) if possible

❌ **DON'T:**
- Hardcode credentials in workflow files
- Commit `.env` files with real credentials
- Share secret values in public forums
- Use personal email passwords (use app passwords)

---

## Advanced Configuration

### Multiple Schedules
Send reports on different days:

```yaml
on:
  schedule:
    - cron: '0 9 * * 1'   # Monday 9 AM UTC
    - cron: '0 9 * * 5'   # Friday 9 AM UTC
```

### Different Timezones per Branch
Use different cron schedules in different branches:
- `main` branch: Production schedule
- `staging` branch: Test schedule

### Conditional Execution
Only run on specific branches:

```yaml
jobs:
  send-email-report:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
```

---

## Migration from Windows Task Scheduler

If you previously set up Windows Task Scheduler:

1. **Disable Windows Task Scheduler:**
   ```powershell
   Disable-ScheduledTask -TaskName "Timesheet-Weekly-Report"
   ```

2. **Set up GitHub Actions** (follow this guide)

3. **Test GitHub Actions** works (manual trigger)

4. **Remove Windows Task** (optional):
   ```powershell
   Unregister-ScheduledTask -TaskName "Timesheet-Weekly-Report" -Confirm:$false
   ```

---

## Getting Help

**GitHub Actions not working?**
1. Check [GitHub Status](https://www.githubstatus.com/)
2. Review [GitHub Actions documentation](https://docs.github.com/en/actions)

**Email issues?**
1. Test SMTP credentials manually
2. Check email provider's documentation
3. Verify firewall/security settings

**Application issues?**
1. Check `services/automated_scheduler.py` logs
2. Verify database settings in Settings page
3. Test with "Send Email Report" button first

---

## Summary Checklist

- [ ] Code pushed to GitHub
- [ ] All 7 secrets added (SUPABASE_URL, SUPABASE_KEY, SMTP_*)
- [ ] Cron schedule adjusted for timezone
- [ ] Manual workflow test successful
- [ ] Email received with correct data
- [ ] Waiting for first scheduled run
- [ ] Monitoring Actions tab for errors

---

**You're all set!** 🎉

GitHub Actions will now automatically send your timesheet reports based on the configured schedule, completely hands-free.

No need to keep your PC on or Streamlit running.
