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

# 🔁 Payment reconciliation (recovering mis-labeled payments)

Sometimes MPESA callbacks arrive but the app did not update the DB (network hiccup, webhook routed to old ngrok URL, or transient errors). To help recover those records we provide a safe reconciliation utility that scans stored `callback_raw_data` and marks payments as `success` when the callback indicates a successful STK result.

Files provided

- `payments/management/commands/reconcile_payments.py` - management command that inspects `Payment.callback_raw_data` and can mark `failed` payments as `success` when the callback payload contains a success ResultCode (non-destructive by default).
- `payments/scripts/find_failed_but_success.py` - quick convenience script to list candidate payments whose stored callback appears successful.
- `payments/scripts/apply_reconcile.py` - one-off script (used internally) to apply reconciliation updates.

Important safety notes

- The command defaults to a dry-run. It will only show what _would_ be changed unless you pass `--apply` (the command in this repo uses `--apply` semantics in `cleanup_failed_payments`; `reconcile_payments` in the codebase also follows a dry-run-first approach).
- Always create a DB backup (or take a snapshot) before applying mass updates in production.
- Reconciliation should be run by an admin or a trusted maintainer only. Access to payment data is sensitive.

Usage examples

Dry-run (see what would be updated):

```bash
# Inspect candidates without changing the DB
python manage.py reconcile_payments --dry-run

# Inspect and limit to N records (useful for testing)
python manage.py reconcile_payments --dry-run --limit 100
```

Apply changes (make updates):

```bash
# Apply reconciliation updates to all candidates
python manage.py reconcile_payments

# Apply but only to newest 50 candidates (safer incremental run)
python manage.py reconcile_payments --limit 50
```

Helper scripts (ad-hoc)

If you prefer to run the small helper script directly from the shell (not recommended for production), you can run the `payments/scripts/find_failed_but_success.py` to list candidates, or `payments/scripts/apply_reconcile.py` to apply fixes. These are convenience scripts intended for maintainers and are not wrapped with the same safety flags as the management command.

```bash
# List candidates (ad-hoc)
python manage.py shell -c "exec(open('payments/scripts/find_failed_but_success.py').read())"

# Apply reconcile script (ad-hoc) — this will modify the DB immediately
python manage.py shell -c "exec(open('payments/scripts/apply_reconcile.py').read())"
```

After reconciliation

- Re-run `python manage.py makemigrations && python manage.py migrate` only if you change models.
- Re-run your test suite (`python manage.py test`) if you made logic changes.

If you want, I can also:

- Add a short admin-only page that lists reconciliation candidates and allows approving changes from the admin UI.
- Add an audit log entry each time a reconciliation changes a `Payment` record (recommended for compliance).

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
* [x] Implemented MPESA utilities: `payments/utils/mpesa_api.py` (includes token caching and safer headers)
* [x] Added MPESA error mapping: `payments/utils/errors.py`
* [x] Implemented MPESA callback endpoint: `payments/views/callback.py` (`/payments/mpesa/callback/`)
* [x] Implemented STK initiation endpoint: `payments/views/initiate.py` (`/payments/initiate/`)
* [x] Wired payment URLs in `payments/urls.py` (`/payments/status/`, `/payments/webhook/`, `/payments/initiate/`, `/payments/mpesa/callback/`)
* [x] Added small validators util: `payments/utils/validators.py`
* [x] Added admin registration for `Payment`, `Profile`, and `PaymentAccessLog` (audit)
* [x] Added management command to create a dev superuser: `users/management/commands/createsu.py`
* [x] Added local accounts workflow: `accounts.example.json` template and `.gitignore` entry for `accounts.json`
* [x] Created and applied migrations for `payments` and `users` (including safe data migration to make `Payment.user` non-nullable)
* [x] Wrote unit tests for MPESA callback and STK initiation (tests pass locally): `payments/tests_mpesa.py`
* [x] Implemented reconciliation & cleanup utilities (management commands and scripts) for failed/test payments
* [x] Implemented `PaymentAccessLog` and server-side access auditing (logs who accessed payment details)
* [x] Implemented unified payment modal (MPesa + Crypto) with live crypto prices, USD→KES conversion, QR generation and copy-to-clipboard
* [x] Added market page improvements and server-side cached `/api/market-prices/` endpoint (caching default 5 minutes)
* [x] Improved payment history UI and details page (filters, pagination, CSV/PDF export, details view styling)
* [x] Added auth templates for login/register/password reset and styled them to match the theme
* [x] Implemented secure POST-based logout using `LogoutView` and `LOGOUT_REDIRECT_URL`
* [x] Integrated Celery + Redis wiring in dev instructions and added example `docker-compose.celery.yml`
* [x] Added clear ngrok usage notes and `NGROK_HOST` handling in `settings_dev.py`
* [x] Added `.env.example` and updated docs to use `cp .env.example .env` (do NOT commit `.env`)

Notes:
- Most of the above work was implemented incrementally while testing locally with ngrok, Celery workers, and the MPESA sandbox.
- Several safety features were added: token caching (process-local), safer request headers to avoid sandbox WAF blocks, and graceful fallbacks for forex/price APIs.


# Project Roadmap (Prioritized)

This is the current roadmap with checkboxes reflecting completed and remaining tasks.

## Phase 1 — Foundation

* [x] Create modular apps and split settings
* [x] Add `.env.example` and `.gitignore` rules (do **not** commit `.env`)
* [x] Move secrets to `.env` (documented; ensure local `.env` is created via `.env.example`)
* [ ] Remove unused scripts & files (cleanup ongoing)
* [ ] Delete commented-out code (cleanup ongoing)

## Phase 2 — Core Backend & MPESA Integration

* [x] MPESA STK initiation & callback endpoints
* [x] Token caching (in-memory process-local) and safer HTTP headers to mitigate sandbox WAF blocks
* [x] Basic retries and tenacity use for transient HTTP errors (tunable)
* [ ] Move token cache to shared cache (Django cache/Redis) — recommended for multi-worker setups
* [ ] Add stricter response schema validation for MPESA responses
* [ ] Add structured logging (JSON logs) for token, STK payloads, and callback events
* [ ] Notifications (email/SMS/push) after payment confirmation (integration required)

## Phase 3 — Backend API & Auth (updates)

We implemented several improvements to secure APIs, provide a consistent JSON error format for API clients, and protect critical endpoints from abuse.

What we implemented:

* [x] Standard JSON error responses for API requests via `core.middleware.json_exception_middleware.JsonExceptionMiddleware`.
  - Behavior: If the request path starts with `/api/` or the client sends `Accept: application/json`, unhandled exceptions return a structured JSON payload:

```json
{ "status": "error", "message": "internal server error", "detail": "...exception text..." }
```

* [x] Rate-limiter decorator `core.utils.permissions.rate_limit` used on the MPESA initiation endpoint to limit by IP address (default: 4 requests / 60s). Example usage:

```python
from core.utils.permissions import rate_limit

@rate_limit('mpesa_initiate', limit=4, period=60)
def initiate_payment(request):
    ...
```

* [x] Owner / admin access decorator `core.utils.permissions.admin_or_owner_required` (and existing `payments.decorators.audit_and_require_payment_view`) to restrict payment detail access to staff or the payment owner and automatically log access to `PaymentAccessLog`.

Notes & how to configure:

* The rate limiter uses Django's cache backend. For local dev this defaults to the in-memory local cache, but for multi-process setups you should configure a shared cache (Redis) in `core/settings_dev.py`:

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {'CLIENT_CLASS': 'django_redis.client.DefaultClient'},
    }
}
```

* If no cache is available, the rate limiter gracefully logs a warning and allows requests (to avoid accidental outages during dev). In production, configure Redis and increase key TTLs as appropriate.

* The JSON error middleware is lightweight — it only returns JSON for API requests (path starts with `/api/` or `Accept: application/json`). For normal HTML pages you will still get Django's debug/404 pages.


## Phase 4 — Database & Auditing

* [x] `PaymentAccessLog` implemented and registered in admin (read-only)
* [ ] Additional DB indexes and constraints (TBD)
* [ ] Audit exports & retention policy

## Phase 5 — Frontend Improvements

* [x] Unified theme scaffolding and scoped landing styles
* [x] Reusable components (cards, forms, buttons) — basic implementations
* [x] Unified combined payment modal with live data
* [x] Payment history UI (search/filter/sort/pagination) and detailed view
* [ ] Further UI polish (icons, hero visuals, mobile-first tweaks)
* [ ] Full dashboard: portfolio, receipts, analytics

## Phase 6 — Git & Workflow

* [x] Added `.gitignore` recommendations and branch guidance in README
* [ ] Adopt strict feature-branch workflow & PR checks (CI) — to do

## Phase 7 — Deployment

* [ ] Dockerfile and production compose
* [ ] Nginx + Gunicorn configuration
* [ ] HTTPS, monitoring, and logging stacks

## Phase 8 — Documentation

* [x] Updated README with setup notes, ngrok guidance, and reconciliation docs
* [ ] API docs / Swagger
* [ ] MPESA flow diagrams & architecture docs

## Phase 9 — Testing Suite

* [x] Unit tests for MPESA flows (callback & STK) — local tests pass
* [ ] Integration tests (end-to-end STK → callback → DB under Celery)
* [ ] Add tests for token caching and retry/backoff


# What to do next (recommended immediate tasks)

1. Move token caching to Django cache/Redis so multiple Celery workers/processes share the same token (high priority for production). — [ ]
2. Add stricter MPESA response schema validation and unit tests for token generation and STK responses. — [ ]
3. Implement structured JSON logging or integrate `structlog` for machine-parsable logs. — [ ]
4. Add notifications (payment_confirmed) via Celery tasks and document required env vars (e.g., TWILIO credentials) in `.env.example`. — [ ]
5. Polish frontend: mobile-first tweaks, hero visuals, and finalize component library (cards/forms/buttons). — [ ]
