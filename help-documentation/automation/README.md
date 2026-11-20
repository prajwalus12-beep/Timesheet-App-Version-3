# Documentation Automation System

This folder contains scripts that keep the Help Documentation synchronized with the application source code.

---

## Scripts

| Script | Purpose |
|--------|---------|
| `doc_sync_engine.py` | Analyzes source code changes and flags affected documentation |
| `screenshot_generator.py` | Captures screenshots from the live application using Playwright |
| `doc_validator.py` | Validates all Markdown links and screenshot references |

---

## How It Works

```
Application Source Code
        │
        ▼
doc_sync_engine.py ──► Detects changes (AST analysis)
        │
        ▼
   Change Report ──► Lists affected modules and documentation files
        │
        ▼
  Manual Review ──► Developer reviews and updates .md files
        │
        ▼
doc_validator.py ──► Validates all links and images
        │
        ▼
screenshot_generator.py ──► Recaptures outdated screenshots
        │
        ▼
   CHANGELOG.md ──► Updated with what changed
```

---

## Running the System

### Step 1: Detect Documentation Drift

```bash
cd "c:\FMP TS\update project include project updatation page\Timesheet-App-Version-3"
python help-documentation/automation/doc_sync_engine.py
```

Output: A report listing changed source files, affected modules, and which documentation files need updating.

### Step 2: Validate Documentation

```bash
python help-documentation/automation/doc_validator.py
```

Output: List of broken links and missing screenshots.

### Step 3: Capture Screenshots

```bash
python help-documentation/automation/screenshot_generator.py --url http://localhost:8501
```

Requires the app to be running (`streamlit run app.py`) and Playwright installed.

### Step 4: Update CHANGELOG.md

Manually add an entry to `help-documentation/CHANGELOG.md` describing what changed and which files were updated.

---

## Installing Playwright (for Screenshots)

```bash
pip install playwright
playwright install chromium
```

---

## Integrating with CI/CD

Add to your CI/CD pipeline (GitHub Actions example):

```yaml
- name: Check Documentation Drift
  run: python help-documentation/automation/doc_sync_engine.py --fail-on-changes
```

This fails the build if undocumented user-facing changes are detected.

---

## Philosophy

- **Never delete** existing accurate documentation — only update affected sections.
- **Never invent** features or validations not present in source code.
- **Flag** changes requiring human review rather than auto-generating unverified docs.
- **Distinguish** between refactoring (no doc update needed) and functional changes (doc update needed).
