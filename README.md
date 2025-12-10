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
# If your Django dev server runs on the default port 8000:
ngrok http 8000

# If you run the server on port 8080 (or another port), start ngrok for that port instead:
ngrok http 8080

# Note: Use the ngrok forwarding URL (https://<your-subdomain>.ngrok-free.dev) as your MPESA callback URL and add that host to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` in your `.env`.


## Quick run with ngrok

If you're testing callbacks with ngrok, set the ngrok host in your shell and start the Django dev server (example):

```bash
export NGROK_HOST=subphrenic-tonda-hipper-ngrok-free.dev
python manage.py runserver
```

This ensures `NGROK_HOST` is available to `settings_dev.py` and your local server accepts requests from the ngrok domain.

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

## Environment (.env)

For local development, copy `.env.example` to `.env` and fill in real values. Do NOT commit your `.env` file — it's already included in `.gitignore`.

```bash
# copy the example and edit
cp .env.example .env
# then open .env and set real values (SECRET_KEY, MPESA keys, etc.)
# example quick edit using nano:
nano .env
```

Example values you should set in `.env`:

```
SECRET_KEY=dev-insecure-secret-key
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
CSRF_TRUSTED_ORIGINS=https://subphrenic-tonda-hipper.ngrok-free.dev

MPESA_CONSUMER_KEY=riGjp64odowDOnvadnjyjeiJUmc4eSDtQeclNKNfXCscICpk
MPESA_CONSUMER_SECRET=fXRp0DR8huY76Bsjog15rX2CAcZ27i19dyu3AtYGYzHorvHWIXDJKUqJCqtGAxsn
MPESA_CALLBACK_URL=https://subphrenic-tonda-hipper.ngrok-free.dev/payments/callback/
MPESA_ENV=sandbox
```

If you prefer to keep secrets in the shell instead of a `.env` file, you can export variables in your shell session instead:

```bash
export MPESA_CONSUMER_KEY=...
export MPESA_CONSUMER_SECRET=...
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

* [x] Add detailed logging for token + STK steps  # TODO: add structured logging
* [x] Implement retry logic                         # TODO: add retry/backoff for transient errors
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
* [x] Integrate Celery + Redis
* [x] Add periodic tasks + retries

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

## 🔒 Sensitive data access & visibility

Payment records contain sensitive personal and financial information (phone numbers, MPESA receipts, callback payloads). Treat access to full payment details as restricted and follow the principle of least privilege.

Who should be allowed to view full payment details

- System administrators (on-duty ops) for debugging and incident response
- Support engineers with approved access for customer support cases (must be time-limited and logged)
- Auditors and compliance officers under a formal request process

Who should NOT have access

- General developers on non-production environments without explicit need
- Unauthenticated users or normal application users (they should only see their own records)
- Third-party contractors without an approved NDA or limited-scope access

Recommended controls and procedures

1. Role-based access control (RBAC)
   - Enforce RBAC on views that return full `callback_raw_data` or `error_message`.
   - Prefer server-side checks (decorators or middleware) instead of hiding data in templates.

2. Logging and auditing
   - Log every access to sensitive payment data (who, when, and why).
   - Store audit logs in an append-only system if possible.

3. Redaction by default
   - In list views or public dashboards, show only minimal fields (amount, date, truncated receipt). Full payloads should be shown only in the detail view to authorized users.

4. Access requests & approvals
   - Require a short justification and approval from a team lead for access to specific production payment records.

5. Data retention & deletion
   - Keep failed test payments separated from production payments.
   - Provide a safe clean-up workflow (see `cleanup_failed_payments` management command) and a retention policy for callback payloads.

6. Encrypt backups and restrict DB access
   - Ensure DB backups are encrypted and restrict access to backups to a small set of operators.


---

# New: Access Auditing & Authorization (Implemented)

To improve operational security and make it safe to inspect payment details, the repository now includes the following server-side features (implemented):

- `payments.models.PaymentAccessLog` (new model)
  - Records every access attempt to a `Payment` detail view (who, when, IP, user-agent, action)
  - Registered in the admin as `PaymentAccessLog` for review

- Authorization rules for `payment_detail`
  - Payment owners (the user who created the payment) can view their own records
  - Staff/superusers can view any record
  - Users with the `payments.view_payment` model permission can view records
  - Unauthorized attempts are recorded in `PaymentAccessLog` and return HTTP 403

- Admin UI
  - `PaymentAccessLog` is registered in `payments/admin.py` (read-only fields) so ops can review access events


## Migration & setup steps (required)

After pulling these code changes you must create and apply migrations to add the `PaymentAccessLog` table:

```bash
# from project root
source crypto/bin/activate     # or your venv
python manage.py makemigrations payments
python manage.py migrate
```

If you use migrations via a CI pipeline, include the generated migration in your PR. The new migration will create the `payments_paymentaccesslog` table.


## How to grant support access

To allow a user to view other users' payment details, either:

1. Make them staff or superuser (quick, but broad):

```bash
python manage.py shell
from django.contrib.auth import get_user_model
User = get_user_model()
u = User.objects.get(username='alice')
u.is_staff = True
u.save()
```

2. Grant the model-level view permission (fine-grained):

```bash
python manage.py shell
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from payments.models import Payment

ct = ContentType.objects.get_for_model(Payment)
perm = Permission.objects.get(content_type=ct, codename='view_payment')
user = get_user_model().objects.get(username='bob')
user.user_permissions.add(perm)
```

This grants only the `view_payment` right which the code checks for access.


## Operational notes

- Audit logs are intentionally stored in the regular DB for now. For production, consider shipping them to a centralized audit/append-only store (WORM or ELK/S3 with restricted ACLs) and add an export-only admin view.

- The audit logger is defensive: logging failures do not interrupt the user request.

- If you need a stricter policy (e.g., support staff must request approval before viewing a record), we can add a simple `approval_required` flag and gate the view until approved.


---
