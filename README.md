# Crypto Sales Page

A small Django project that serves a simple frontend for showcasing cryptocurrency information. The project contains a `frontend` Django app with static assets and a template at the root URL.

Tech stack
- Python 3.10+ / 3.12
- Django
- Plain JavaScript/CSS for frontend assets

Why this README
- Help you get the project running locally quickly
- Document where static assets and templates live
- Show common development commands

Quickstart (local)

1. Use the included virtual environment (optional)

If you want to use the environment bundled in the repository, activate it:

```bash
# activates the existing virtualenv located at `crypto/`
source crypto/bin/activate
```

If you prefer to create a fresh venv:

```bash
python -m venv .venv
source .venv/bin/activate
```

2. Install dependencies

If a `requirements.txt` exists, install it; otherwise install Django:

```bash
# If requirements.txt exists
pip install -r requirements.txt

# Or, at minimum
pip install django
```

3. Apply migrations and create (optional) superuser

```bash
python manage.py migrate
python manage.py createsuperuser  # optional
```

4. Run the dev server

```bash
python manage.py runserver
```

Open http://127.0.0.1:8000/ in your browser — the `frontend` app is routed at the root URL.

Project layout (high level)
- core/ — Django project settings and URL routing
- frontend/ — Django app that contains views, templates, and static assets
  - templates/frontend/index.html
  - static/frontend/crypto.js, crypto.css, images/
- db.sqlite3 — default SQLite DB for development (if present)

Common commands

```bash
# Run tests
python manage.py test

# Make migrations
python manage.py makemigrations

# Collect static files for production
python manage.py collectstatic
```

Notes and tips
- Keep `SECRET_KEY` out of source control for production; use environment variables for secrets.
- Set `DEBUG=False` and configure `ALLOWED_HOSTS` for production deployments.
- The repo includes a `crypto/` directory which looks like a Python virtual environment; you can use it or create a new one.

Contributing
- Create a branch per feature/fix
- Add tests for new behaviour
- Open a pull request describing your change

Repository
- Remote: https://github.com/danielmaina989/crypto-sales-page.git
- Default branch: main

License
- MIT — see the `LICENSE` file for details.

Contact
- If this is your personal project, add your contact or repo remote URL here.

---

# DETAILED TO-DO LIST FOR PROJECT IMPROVEMENT

Below is the actionable, step-by-step to-do list to improve the project. Use this as the canonical checklist inside the repository README to track work.

# ✅ DETAILED TO-DO LIST FOR PROJECT IMPROVEMENT

---

## 1. Codebase Cleanup & Structure

### 1.1 Organize project folders

* [x] Create `core/` folder for main business logic
* [x] Create `payments/` folder for MPESA integration files
* [x] Create `users/` module for authentication & user management
* [x] Separate `settings.py` into:

  * [x] `base.py`
  * [x] `dev.py`
  * [x] `prod.py`


*Notes:*
- Admin registration added for `payments.Payment` and `users.Profile` (see `payments/admin.py` and `users/admin.py`).
- Superuser creation helper management command added: `python manage.py createsu` (reads DEV_SUPERUSER_USERNAME, DEV_SUPERUSER_EMAIL, DEV_SUPERUSER_PASSWORD env vars or uses defaults).
- Migrations: models are present and were used in tests; if you want persistent migrations committed, run `python manage.py makemigrations payments users` and commit the generated files under each app's `migrations/` folder.

### 1.2 Remove unused files

* [ ] Delete old scripts not used
* [ ] Remove commented-out code

### 1.3 Add environment variable support

* [ ] Create `.env`
* [ ] Move API keys and passwords from code → .env
* [ ] Add `.env.example`

---

## 2. MPESA Integration Improvement

### 2.1 Fix STK push flow

* [ ] Add clear logging at each step
* [ ] Add retry mechanism for failed token or STK requests
* [ ] Validate response payloads

### 2.2 Implement webhook endpoint

* [ ] Create `mpesa/callback/` endpoint
* [ ] Validate callback body
* [ ] Update payment status in DB
* [ ] Send user notification after success

### 2.3 Add testing mode

* [ ] Create mock data for testing without hitting real API
* [ ] Build unit tests for:

  * [ ] token generation
  * [ ] stk push request
  * [ ] callback handling

---

## 3. Backend API Improvements

### 3.1 Add structured API responses

* [ ] Create a standard JSON formatter
* [ ] Add error handler middleware

### 3.2 Add Auth Improvements

* [ ] Setup JWT or session-based auth
* [ ] Add rate limiting to login endpoint

### 3.3 Add background task system

* [ ] Configure Celery + Redis properly
* [ ] Add periodic tasks
* [ ] Ensure failed tasks are logged and retried

---

## 4. Database Optimization

### 4.1 Create missing indexes

* [ ] Add index on user email
* [ ] Add index on payment reference
* [ ] Add index on status fields

### 4.2 Add constraints

* [ ] Unique constraint for transaction IDs
* [ ] Foreign key checks

### 4.3 Design new tables if needed

* [ ] Payment audit table
* [ ] Logs table

---

## 5. Frontend Cleanup / UI Improvement

### 5.1 Improve UI consistency

* [ ] Define color palette
* [ ] Standardize fonts
* [ ] Add reusable button & alert components

### 5.2 Improve forms

* [ ] Add validation feedback
* [ ] Add loading indicators
* [ ] Disable submit button during processing

### 5.3 User dashboard

* [ ] Payment status display
* [ ] Download receipts
* [ ] Profile settings

---

## 6. Git / Version Control Improvements

### 6.1 Clean up Git history

* [ ] Remove large/unnecessary files
* [ ] Add `.gitignore` rules

### 6.2 Introduce Git Flow

* [ ] Create `dev` branch
* [ ] Use feature branches per task
* [ ] Merge using pull requests

---

## 7. Deployment

### 7.1 Docker setup

* [ ] Create Dockerfile
* [ ] Add docker-compose:

  * [ ] web
  * [ ] db
  * [ ] redis
  * [ ] celery

### 7.2 Production server

* [ ] Nginx reverse proxy
* [ ] Gunicorn for backend
* [ ] SSL setup

### 7.3 Monitoring

* [ ] Add logs using `loguru` or Django logging
* [ ] Add uptime monitor (UptimeRobot)
* [ ] Add email alerts for failures

---

## 8. Documentation

### 8.1 Setup README

* [ ] Setup instructions
* [ ] Environment config
* [ ] How to run tests

### 8.2 Create API documentation

* [ ] Postman collection
* [ ] Swagger / DRF docs

### 8.3 Payment flow diagram

* [ ] Sequence diagram for MPESA STK

---

## 9. Testing

### 9.1 Unit tests

* [ ] Users
* [ ] Payments
* [ ] Tasks

### 9.2 Integration tests

* [ ] STK push
* [ ] Callback
* [ ] Authentication

### 9.3 Manual test checklist

* [ ] Registration
* [ ] Login
* [ ] Payment initiation
* [ ] Payment confirmation
* [ ] Error cases

---

## Local accounts file (secrets - DO NOT COMMIT)

This project supports a local `accounts.json` file for development-only accounts or service credentials. The repository includes a safe example you can copy:

- `accounts.example.json` — checked-in template with placeholder values.
- `accounts.json` — local file (added to `.gitignore`) where you keep real credentials for local development.

Quick start
1. Copy the example:

```bash
cp accounts.example.json accounts.json
# Edit accounts.json with real local values, DO NOT commit it
```

2. Load accounts from Python using the helper:

```python
from core.utils.accounts import load_accounts
accounts = load_accounts()
admin = accounts.get('admin')
```

Security note
- `accounts.json` is intentionally ignored by git; never commit real secrets. For production, use environment variables or a secrets manager instead.

---

Next steps
- This README now contains your full checklist. To start work pick one top-level section (for example: `1. Codebase Cleanup & Structure`) and open a new feature branch.
- If you'd like, I can create issue templates, a GitHub Projects board, or convert each bullet into a tracked issue/PR template.

Notes
- `requirements.txt` already contains Django pinned to `Django==5.2.9`; pin additional dependencies as you add them.
- The project already includes a `LICENSE` file at the repository root (MIT). Add your repo remote URL in the Contact section if it differs.
