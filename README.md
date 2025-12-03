# 🚀 Crypto Sales Page

A Django-based project that serves a simple frontend for showcasing cryptocurrency information. The project includes a `frontend` app with static assets and a template routed at the root URL.

---

## 🧱 Tech Stack

* **Python** 3.10–3.12
* **Django**
* **SQLite** (development)
* **Plain JavaScript/CSS** for frontend assets

---

## 📌 Why this README Exists

This document helps you:

* Run the project locally
* Understand the file layout
* Follow best practices for development
* Track improvements using a structured roadmap

---

# ⚡ Quickstart (Local Development)

### **1. Activate Virtual Environment**

Use the provided virtualenv:

```bash
source crypto/bin/activate
```

**Or create a new one:**

```bash
python -m venv .venv
source .venv/bin/activate
```

---

### **2. Install Dependencies**

```bash
pip install -r requirements.txt
```

Or minimally:

```bash
pip install django
```

---

### **3. Run Migrations**

```bash
python manage.py migrate
python manage.py createsuperuser  # optional
```

---

### **4. Start Dev Server**

```bash
python manage.py runserver
```

Open **[http://127.0.0.1:8000/](http://127.0.0.1:8000/)** in your browser.

---

# 🗂️ Project Structure

```
core/                 # Project configuration + settings
frontend/             # Templates, static assets, and views
  ├── templates/frontend/index.html
  └── static/frontend/*.js, *.css, images/
db.sqlite3            # Dev database (optional)
crypto/               # Optional virtualenv
```

---

# 🔧 Common Commands

```bash
python manage.py test
python manage.py makemigrations
python manage.py collectstatic
```

---

# ⚠️ Notes & Best Practices

* **Never commit secrets.** Use environment variables.
* Set **DEBUG=False** in production.
* Configure **ALLOWED_HOSTS** for deployment.
* Use `.env` for local configuration and `.env.example` for documentation.

---

# 🤝 Contributing

* Use feature branches
* Write tests for new features
* Open descriptive pull requests

---

# 🔗 Repository Info

* Remote: [https://github.com/danielmaina989/crypto-sales-page.git](https://github.com/danielmaina989/crypto-sales-page.git)
* Default branch: `main`
* License: **MIT**

---

# 🧭 PROJECT ROADMAP (PRIORITIZED)

This is the cleaned-up, GitHub-friendly version of your to-do list based on the recommended project phases.

---

# Accomplishments to date

The following features and tasks have been implemented and tested in this repository so far:

* [x] Created modular apps: `core/`, `payments/`, `users/`
* [x] Split settings into `base.py`, `dev.py`, `prod.py`
* [x] Added `payments.Payment` model with MPESA-related fields and indexes
* [x] Implemented MPESA utilities: `payments/utils/mpesa_api.py`
* [x] Added MPESA error mapping: `payments/utils/errors.py`
* [x] Implemented MPESA callback endpoint: `payments/views/callback.py` (`/payments/mpesa/callback/`)
* [x] Implemented STK initiation endpoint: `payments/views/initiate.py` (`/payments/initiate/`)
* [x] Wired payment URLs in `payments/urls.py` (`/payments/status/`, `/payments/webhook/`, `/payments/initiate/`, `/payments/mpesa/callback/`)
* [x] Added small validators util: `payments/utils/validators.py`
* [x] Added admin registration for `Payment` and `Profile`
* [x] Added management command to create a dev superuser: `users/management/commands/createsu.py`
* [x] Added local accounts workflow: `accounts.example.json` template and `.gitignore` entry for `accounts.json`
* [x] Created and applied migrations for `payments` and `users` (including safe data migration to make `Payment.user` non-nullable)
* [x] Wrote unit tests for MPESA callback and STK initiation (tests pass locally): `payments/tests_mpesa.py`
* [x] Ran full test suite locally — all tests pass
* [x] Committed all new files and migrations in the local repository

Notes
- Some roadmap items remain (detailed logging, retry logic, webhook hardening, `.env` support, Celery integration, etc.). See the roadmap below for remaining priorities.
- `payments/utils/mpesa_api.py` will attempt to use `requests` for real API calls; in environments without `requests` installed the module raises a clear RuntimeError — add `requests` to `requirements.txt` if you plan to call MPESA from this environment.

---

# 🟦 Phase 1 — Foundation (Highest Priority)

## **1. Project Structure & Cleanup**

* [x] Create modular apps: `core/`, `payments/`, `users/`
* [x] Split settings into:

  * `base.py`
  * `dev.py`
  * `prod.py`
* [ ] Remove unused scripts and files
* [ ] Delete commented-out code
* [ ] Add `.env` & `.env.example`
* [ ] Move secrets (keys/passwords) into `.env`

**Notes:**
Admin registration for models added.
Optional helper command exists: `python manage.py createsu`.

---

# 🟩 Phase 2 — Core Backend & MPESA Integration

## **2. MPESA STK Push Improvements**

* [ ] Add detailed logging for token + STK steps  # TODO: add structured logging
* [ ] Implement retry logic                         # TODO: add retry/backoff for transient errors
* [ ] Validate API responses                        # TODO: add strict response schema validation

### Webhook

* [x] Create `/mpesa/callback/` endpoint            # Implemented: `payments/views/callback.py`
* [x] Validate callback body                        # Implemented: basic JSON parsing and presence checks; returns 400 on invalid JSON
* [x] Update payment status in DB                   # Implemented: updates `Payment.status`, `mpesa_receipt_number`, `error_*` fields
* [ ] Notify user                                   # TODO: integrate notifications (email/SMS/push)

### Testing Mode

* [x] Mock MPESA responses                         # Implemented in tests using `unittest.mock.patch`
* [x] Tests for:

  * [ ] Token generation                            # Not implemented yet
  * [x] STK requests                                # Implemented: `payments/tests_mpesa.py` mocks `initiate_stk_push`
  * [x] Callback processing                         # Implemented: `payments/tests_mpesa.py` includes success & failure callback tests

---

# 🟧 Phase 3 — Backend API & Auth

## **3. Backend Enhancements**

* [ ] Standard JSON response structure
* [ ] Global error handler middleware
* [ ] JWT or session-based authentication
* [ ] Add rate limiting
* [ ] Integrate Celery + Redis
* [ ] Add periodic tasks + retries

---

# 🟨 Phase 4 — Database Optimization

* [ ] Add DB indexes
* [ ] Transaction ID unique constraint
* [ ] Add audit tables
* [ ] Add logs table

---

# 🟪 Phase 5 — Frontend Improvements

* [ ] Define UI theme (colors, fonts)
* [ ] Create reusable UI components
* [ ] Improve forms (validation, loading states)
* [ ] Build user dashboard:

  * Payment history
  * Download receipts
  * Profile settings

---

# 🟫 Phase 6 — Git & Workflow

* [ ] Expand `.gitignore`
* [ ] Clean large/unnecessary files
* [ ] Add `dev` branch
* [ ] Use feature branches
* [ ] Merge using PRs

---

# 🟦 Phase 7 — Deployment

* [ ] Dockerfile
* [ ] docker-compose (web + db + redis + celery)
* [ ] Nginx reverse proxy
* [ ] Gunicorn
* [ ] HTTPS/SSL
* [ ] Logging + uptime monitoring

---

# 🟩 Phase 8 — Documentation

* [ ] Improve setup instructions
* [ ] Add environment configuration guide
* [ ] Write API docs (Swagger / Postman)
* [ ] Add MPESA flow diagram

---

# 🟧 Phase 9 — Testing Suite

* [ ] Unit tests (users, payments, tasks)
* [ ] Integration tests (STK → callback → DB)
* [ ] Manual test checklist

---

# 🔐 Local Accounts File (DO NOT COMMIT)

Use:

* `accounts.example.json` → safe template
* `accounts.json` → your private local secrets (ignored by git)

Example usage:

```bash
cp accounts.example.json accounts.json
```

Python loader:

```python
from core.utils.accounts import load_accounts
accounts = load_accounts()
```

---

# Running with Celery (optional)

A minimal docker-compose example to run the Django app with a Redis broker and a Celery worker is provided in `docker-compose.celery.yml`.

Quick start (requires Docker):

```bash
docker-compose -f docker-compose.celery.yml up --build
```

This brings up Redis, the web app (Gunicorn), and a `worker` service running Celery.

Locally without Docker, to run a worker:

```bash
# ensure you have redis running locally
export CELERY_BROKER_URL=redis://localhost:6379/0
export CELERY_RESULT_BACKEND=$CELERY_BROKER_URL
# start worker
celery -A core.celery.app worker --loglevel=info
```

Notes:
- `core/celery.py` contains a lightweight Celery factory; Celery is optional. If Celery is not installed the project still works, and `payments.tasks.poll_payment_status` is a synchronous fallback.

---
