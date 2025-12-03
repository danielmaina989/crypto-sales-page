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

* [ ] Add detailed logging for token + STK steps
* [ ] Implement retry logic
* [ ] Validate API responses

### Webhook

* [ ] Create `/mpesa/callback/` endpoint
* [ ] Validate callback body
* [ ] Update payment status in DB
* [ ] Notify user

### Testing Mode

* [ ] Mock MPESA responses
* [ ] Tests for:

  * Token generation
  * STK requests
  * Callback processing

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
