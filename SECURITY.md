# 🔒 Security Policy & Incident Response

This document outlines security practices and incident response procedures for the crypto-sales-page project.

---

## ⚠️ Incident: Exposed Sandbox Credentials (Dec 3, 2025)

### What Happened
Sandbox credentials (M-Pesa Consumer Key, Secret, and Passkey) were committed to the git repository and exposed publicly on GitHub.

### Affected Credentials (REVOKED)
- Consumer Key: `riGjp64odowDOnvadnjyjeiJUmc4eSDtQeclNKNfXCscICpk` ❌
- Consumer Secret: `fXRp0DR8huY76Bsjog15rX2CAcZ27i19dyu3AtYGYzHorvHWIXDJKUqJCqtGAxsn` ❌
- Passkey: `bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919` ❌

**Status**: REVOKED on Daraja. New credentials generated.

### Root Cause
- `.env` file committed accidentally to git
- Hardcoded credentials in `mpesa_test.py`
- `.gitignore` rule existed but `.env` was already tracked by git

### Remediation Completed
1. ✅ `.env` removed from git history (pending force push)
2. ✅ Hardcoded credentials removed from `mpesa_test.py` (loads from `.env` instead)
3. ✅ Old credentials revoked on Daraja
4. ✅ New credentials generated and stored in local `.env` (gitignored)
5. ✅ This security policy document created

### If You Cloned Before Dec 3, 2025
```bash
# Your local clone may have the exposed .env
# Simply delete it and recreate from .env.example:
rm -f .env
cp .env.example .env
# Then add your NEW credentials (generated after credential rotation)
```

---

## 🛡️ Best Practices

### 1. Never Commit Secrets

**❌ DON'T:**
```python
# ❌ BAD: Hardcoded in code
MPESA_CONSUMER_KEY = "my-real-key"
SECRET_KEY = "django-secret"
DATABASE_PASSWORD = "prod-password"
```

**✅ DO:**
```python
# ✅ GOOD: Load from environment
import os
MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
SECRET_KEY = os.getenv("SECRET_KEY")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
```

### 2. Use `.gitignore` Correctly

Ensure these lines are in `.gitignore`:
```
.env
.env.local
.env.*.local
*.key
*.pem
accounts.json
db.sqlite3
```

### 3. Use `.env.example` for Documentation

**❌ DON'T:**
```
MPESA_CONSUMER_KEY=your-real-key-here  # ← This defeats the purpose
```

**✅ DO:**
```
# .env.example (commit this file)
MPESA_CONSUMER_KEY=YOUR_MPESA_CONSUMER_KEY  # Placeholder, no real value
MPESA_CONSUMER_SECRET=YOUR_MPESA_CONSUMER_SECRET
```

### 4. Rotate Credentials Regularly

- Sandbox: Rotate every 6 months or after any exposure
- Production: Rotate every 30-90 days
- After any suspected compromise: Rotate immediately

### 5. Use Different Credentials for Each Environment

```
Development:  sandbox credentials (rotate on exposure)
Staging:      staging credentials (rotate monthly)
Production:   production credentials (rotate quarterly + on exposure)
```

**Never use production credentials in development.**

### 6. Enable Branch Protection

On GitHub, protect your main branch:
- Require pull request reviews
- Require status checks before merge
- Enable "Dismiss stale PR approvals" 

This prevents accidental commits of `.env` or other secrets.

### 7. Use Git Hooks to Prevent Secrets

Add a pre-commit hook to catch secrets:

```bash
#!/bin/bash
# .git/hooks/pre-commit

# Prevent committing .env
if git diff --cached --name-only | grep -E '\.env|\.key|accounts\.json'; then
    echo "❌ ERROR: Attempting to commit sensitive files!"
    echo "   Remove these files from staging and re-run git commit:"
    echo "   git reset HEAD .env accounts.json"
    exit 1
fi

# Prevent committing hardcoded secrets (basic check)
if git diff --cached | grep -iE 'SECRET_KEY.*=|PASSWORD.*=|MPESA_CONSUMER_KEY.*=' | grep -v .env.example; then
    echo "❌ WARNING: Possible hardcoded secret detected!"
    echo "   Please review your changes before committing."
    exit 1
fi

exit 0
```

Install:
```bash
cp scripts/pre-commit-hook .git/hooks/pre-commit
chmod +x .git/hooks/pre-commit
```

### 8. Monitoring & Alerts

- Enable GitHub Dependabot alerts for vulnerable dependencies
- Use tools like `git-secrets` or `truffleHog` to scan history
- Monitor for unauthorized access to Daraja

---

## 🔄 Responding to a Credentials Breach

If credentials are exposed:

### Immediate (< 5 minutes)
1. **Revoke immediately** on the provider (Daraja, GitHub, etc.)
2. **Generate new credentials**
3. **Update local `.env` with new credentials**

### Short-term (< 1 hour)
1. **Remove from git history** using BFG or `git filter-branch`
2. **Force push** to GitHub (if public repo)
3. **Check git logs** for other exposed secrets
4. **Audit code** for hardcoded values

### Long-term (< 24 hours)
1. **Rotate all credentials** (not just the exposed ones)
2. **Review access logs** on the service (Daraja, payment provider)
3. **Document incident** in this file (what was exposed, when, actions taken)
4. **Update team practices** to prevent recurrence

### Example Response (M-Pesa Sandbox)
```bash
# 1. Go to https://developer.safaricom.co.ke/
# 2. Delete the exposed app or revoke credentials
# 3. Create NEW credentials
# 4. Update local .env
# 5. Clean git history
bash scripts/revoke_credentials.sh
# 6. Force push
git push -f origin main
```

---

## 🚀 Deployment Security

### Production Environment

**Never use `.env` files in production.** Instead:

1. **Use environment variables** (set in deployment platform):
   - AWS: Secrets Manager, Parameter Store
   - Heroku: Config Vars
   - Docker: Secrets, mounted volumes
   - Kubernetes: Secrets

2. **Use a secrets vault**:
   - HashiCorp Vault
   - AWS Secrets Manager
   - Azure Key Vault

3. **Enable audit logging**:
   - Who accessed which secrets?
   - When were they rotated?
   - Any unauthorized attempts?

### Example: Heroku Deployment

```bash
# Set environment variables (never commit to git)
heroku config:set MPESA_CONSUMER_KEY=your-prod-key
heroku config:set MPESA_CONSUMER_SECRET=your-prod-secret
heroku config:set SECRET_KEY=your-django-secret
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS=your-production-domain.com

# Verify (doesn't print values, just shows they're set)
heroku config
```

---

## 📋 Security Checklist

- [ ] `.env` is in `.gitignore`
- [ ] `.env.example` exists with placeholder values only
- [ ] No hardcoded credentials in `.py` files
- [ ] All secrets loaded from environment variables
- [ ] Pre-commit hooks installed to catch secrets
- [ ] Branch protection enabled on main
- [ ] Different credentials for dev/staging/prod
- [ ] Credentials rotated after any suspected compromise
- [ ] Git history cleaned if secrets were ever committed
- [ ] Production uses secrets manager (not `.env` files)
- [ ] Audit logging enabled for credential access
- [ ] Team educated on security best practices

---

## 📞 Reporting Security Issues

If you discover a security vulnerability:

1. **Do NOT open a public issue on GitHub**
2. **Email**: (contact info to be added)
3. **Include**:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if available)

We will respond within 24 hours and coordinate a fix.

---

## 📚 References

- [OWASP: Secrets Management](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html)
- [GitHub: Removing Sensitive Data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository)
- [Python-dotenv Documentation](https://github.com/theskumar/python-dotenv)
- [Daraja API Security](https://developer.safaricom.co.ke/docs)

---

**Last Updated**: December 3, 2025  
**Status**: Incident resolved, new credentials in use
