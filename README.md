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

# Start Redis server first if not running

```bash
redis-server
```

# Start Celery worker

Run these from the project root (where `manage.py` lives). Use the actual Celery app module paths that exist in the repo:

```bash
# Full app path (common pattern if Celery instance is named `app` in core/celery.py)
celery -A core.celery.app worker --loglevel=info

# Shorter form if the app variable name is `app` in core/celery.py
celery -A core.celery worker -l info
```

# Start periodic tasks (beat) if using scheduled checks

```bash
celery -A core.celery.app beat -l info
```

---
Start the Required Services
Terminal 1 — Django
python manage.py runserver

Terminal 2 — Redis
redis-server


(You already have Redis running.)

Terminal 3 — Celery Worker
celery -A core worker -l info

Terminal 4 — Ngrok (for callbacks)
ngrok http 8000


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

# 🧹 Cleanup & Maintenance

## Clean up failed test payments

After testing MPESA flows, your database may accumulate failed payment records. Use the cleanup command to safely remove or recover them:

```bash
# Dry-run: see what would be changed (default)
python manage.py cleanup_failed_payments

# Mark failed payments WITH receipts as success (they actually succeeded but weren't recorded)
python manage.py cleanup_failed_payments --apply

# Delete failed test payments WITHOUT receipts
python manage.py cleanup_failed_payments --apply --delete-tests

# Only operate on payments older than 7 days
python manage.py cleanup_failed_payments --apply --delete-tests --age-days 7
```

The command is safe:
- **Always shows a summary first** (what would be changed).
- **Requires `--apply` flag** to actually delete/modify records.
- **Default is dry-run**, so you can safely inspect before committing changes.
- **Marks as success** if the payment has a receipt (actually succeeded but callback didn't update DB).
- **Deletes** only if explicitly requested with `--delete-tests` and the payment has no receipt.

---

# ⚠️ Notes & Best Practices

### Security

* **Never commit `.env` with secrets.** Use `.gitignore`:
  ```
  .env
  *.key
  accounts.json
  ```
* **Rotate sandbox credentials if exposed.** Even sandbox credentials should not be public—if you see them in git logs, regenerate them on Daraja.
* **Keep `DEBUG=False` in production.** Never expose stack traces publicly.
* **Configure `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS`** for any public domains (e.g., ngrok URLs during development).

### MPESA Callbacks

* **Callback URLs must be stable.** If using ngrok, pay for a stable subdomain or use a persistent local tunnel—URLs that change will cause M-Pesa to post callbacks to the old URL, and payments will show as failed even though they succeeded.
* **Callbacks are fire-and-forget.** M-Pesa doesn't retry if your server returns an error, so ensure your `/payments/callback/` endpoint always returns 200, even if processing takes time. Use background tasks (Celery) for heavy processing.

### Environment Variables

* Store all secrets in `.env` (never in `.py` files):
  ```
  SECRET_KEY=your-secret-here
  DEBUG=True
  MPESA_CONSUMER_KEY=your-key
  MPESA_CONSUMER_SECRET=your-secret
  MPESA_CALLBACK_URL=https://your-domain/payments/callback/
  ```
* Create `.env.example` with dummy values for documentation:
  ```bash
  cp .env.example .env
  # then edit .env with your real credentials
  ```

---

# 🤝 Contributing

* Use feature branches
* Write tests for new features
* Open descriptive pull requests
* **Review [SECURITY.md](SECURITY.md) before handling credentials or secrets**

---

# 🔐 Security

This project handles sensitive data (MPESA credentials, Django secrets). Please review [SECURITY.md](SECURITY.md) for:
- Best practices for storing secrets
- Incident response procedures
- Credential rotation guidelines
- Pre-commit hooks to prevent accidental leaks

**If you discover a security vulnerability, do NOT open a public issue.** See SECURITY.md for reporting instructions.

---

# 🔗 Repository Info

* Remote: [https://github.com/danielmaina989/crypto-sales-page.git](https://github.com/danielmaina989/crypto-sales-page.git)
* Default branch: `main`
* License: **MIT**

---

# 🧭 PROJECT ROADMAP (PRIORITIZED)

This is the cleaned-up, GitHub-friendly version of your to-do list based on the recommended project phases.

---

## Legend

Use emoji for clearer status at-a-glance:

- ✅ = Done
- ⬜ = Pending / To do
- ❗ = Attention required

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

* ✅ Create modular apps: `core/`, `payments/`, `users/`
* ✅ Split settings into:

  * `base.py`
  * `dev.py`
  * `prod.py`
* ⬜ Remove unused scripts and files
* ⬜ Delete commented-out code
* ✅ Add `.env` & `.env.example`
* ✅ Move secrets (keys/passwords) into `.env`

**Notes:**
- `.env.example` exists at the project root with placeholder values (do NOT commit your real `.env`).
- `core/settings_base.py` includes a small `.env` loader that reads `.env` into the environment for local development.

### Security & env (completed)

* ✅ Added `SECURITY.md` with incident response and best-practices.
* ✅ Added remediation scripts in `scripts/` (`remediate.sh`, `revoke_credentials.sh`) to help rotate and remove exposed credentials.
* ✅ Updated `mpesa_test.py` to load credentials from `.env` (no hardcoded keys).

---

# 🟩 Phase 2 — Core Backend & MPESA Integration

## **2. MPESA STK Push Improvements**

* ✅ Add detailed logging for token + STK steps  # Implemented: structured JSON-style logging helper and safe/redacted logs in `payments/utils/mpesa_api.py`
* ✅ Implement retry logic                         # Implemented: safe retry loops and tenacity integration with `reraise=True`; token and STK calls retry with exponential backoff
* ✅ Validate API responses                        # Implemented: strict response shape validation for token and STK responses; logs and raises on invalid shapes

### Webhook

* ✅ Create `/mpesa/callback/` endpoint            # Implemented: `payments/views/callback.py`
* ✅ Validate callback body                        # Implemented: tolerant parsing and presence checks; returns 200 to acknowledge receipt
* ✅ Update payment status in DB                   # Implemented: updates `Payment.status`, `mpesa_receipt_number`, `error_*` fields
* ✅ Notify user                                   # Implemented: background notification task `payment_notify_user` (Celery shared task + sync fallback) and integration in callback/poller

### Testing Mode

* ✅ Mock MPESA responses                         # Implemented in tests using `unittest.mock.patch`
* ✅ Tests for:

  * ✅ Token generation                            # Implemented: `payments/tests/test_mpesa_token.py` (success / invalid JSON / HTTP error)
  * ✅ STK requests                                # Implemented: `payments/tests_mpesa.py` and additional token tests
  * ✅ Callback processing                         # Implemented: callback tests exist and pass locally


### Notifications (how to enable)

The project includes a background notification task `payment_notify_user` which uses `payments.utils.notifications.notify_payment_success`.

To enable email notifications:

1. Configure Django email settings in your `.env` or environment (example using Gmail SMTP):

```
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@example.com
EMAIL_HOST_PASSWORD=your-email-password
DEFAULT_FROM_EMAIL=your-email@example.com
```

To enable SMS (Twilio):

```
TWILIO_ACCOUNT_SID=your_twilio_sid
TWILIO_AUTH_TOKEN=your_twilio_auth_token
TWILIO_FROM_NUMBER=+1234567890
```

The notifier will attempt to send email to the `payment.user.email` (if present) and the configured `DEFAULT_FROM_EMAIL`. Twilio SMS will be used if the Twilio client is installed and the required env vars are set; otherwise SMS is skipped silently.

### Running the new tests

Run the payments-specific tests locally:

```bash
# Run the payments test module
python manage.py test payments

# Run the token tests only
python manage.py test payments.tests.test_mpesa_token
```

### Notes & Remaining work

* ⬜ Move the in-memory process-local access token cache to a shared cache (Django cache / Redis) so multiple workers/processes reuse the same token and avoid excessive token requests (recommended for production/Celery setups).
* ⬜ Add more comprehensive integration tests for end-to-end STK → callback → DB flows under Celery (including transient network failures and rate-limit scenarios).
* ⬜ Consider exporting true structured JSON logs (using a JSON formatter or structlog) so logs are parsable by log aggregation systems.
* ⬜ Add metrics/monitoring (Sentry/Prometheus) for MPESA errors and token failures.

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
# start worker (use the Celery app module that exports `app`)
celery -A core.celery worker -l info
```

Common mistake: specifying the wrong module in `-A` causes "Unable to load celery application" (for example `-A crypto_sales_page` will fail if no module named `crypto_sales_page` exposes a Celery instance). If you see that error, point `-A` at `core.celery` (the project Celery app) or the module where your Celery `app` lives.

---

## Required .env variables (local development)

This project expects a `.env` file at the project root for local development. These variables are required for MPESA integration and running the site locally. Do NOT commit `.env` into source control — it's already added to `.gitignore`.

Provide values in your local `.env`. Example (use real values only locally):

```
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://example.ngrok-free.dev

# DB (default: SQLite)
DATABASE_URL=sqlite:///db.sqlite3

# MPESA Sandbox (placeholders) - these values are required for MPESA calls
MPESA_CONSUMER_KEY=YOUR_MPESA_CONSUMER_KEY
MPESA_CONSUMER_SECRET=YOUR_MPESA_CONSUMER_SECRET
MPESA_SHORTCODE=174379
MPESA_PASSKEY=YOUR_MPESA_PASSKEY
MPESA_CALLBACK_URL=https://your-ngrok-domain/payments/callback/
MPESA_ENV=sandbox

# Redis / Celery (optional)
REDIS_URL=redis://127.0.0.1:6379/0
```

If you need to share a template, create `.env.example` with placeholder values and commit that instead of `.env`.

---
