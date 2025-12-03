#!/bin/bash
# SECURITY: Revoke exposed sandbox credentials and clean git history
# Run this script IMMEDIATELY after credentials are exposed

set -e

echo "🔒 MPESA Sandbox Credential Revocation Script"
echo "=============================================="
echo ""
echo "⚠️  CRITICAL: Your sandbox credentials were exposed on GitHub!"
echo ""
echo "This script will:"
echo "  1. Remove .env from git history (requires BFG or git filter-branch)"
echo "  2. Guide you through revoking credentials on Daraja"
echo "  3. Remove hardcoded credentials from mpesa_test.py"
echo ""

read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Aborted."
    exit 1
fi

# Step 1: Remove .env from git history
echo ""
echo "📋 Step 1: Remove .env from git history"
echo "=========================================="
echo ""
echo "Option A (RECOMMENDED): Use BFG Repo-Cleaner"
echo "  1. Install BFG: brew install bfg (or download from https://rtyley.github.io/bfg-repo-cleaner/)"
echo "  2. Run: bfg --delete-files .env"
echo "  3. Run: git reflog expire --expire=now --all && git gc --prune=now --aggressive"
echo "  4. Force push: git push -f origin main"
echo ""
echo "Option B (DIY): Use git filter-branch"
echo "  git filter-branch --tree-filter 'rm -f .env' -f -- --all"
echo "  git reflog expire --expire=now --all && git gc --prune=now --aggressive"
echo "  git push -f origin main"
echo ""

# Step 2: Revoke credentials
echo ""
echo "🔑 Step 2: Revoke credentials on Daraja"
echo "======================================"
echo ""
echo "EXPOSED CREDENTIALS:"
echo "  Consumer Key:    riGjp64odowDOnvadnjyjeiJUmc4eSDtQeclNKNfXCscICpk"
echo "  Consumer Secret: fXRp0DR8huY76Bsjog15rX2CAcZ27i19dyu3AtYGYzHorvHWIXDJKUqJCqtGAxsn"
echo "  Passkey:         bfb279f9aa9bdbcf158e97dd71a467cd2e0c893059b10f78e6b72ada1ed2c919"
echo ""
echo "ACTION ITEMS:"
echo "  1. Go to https://developer.safaricom.co.ke/"
echo "  2. Log in with your account"
echo "  3. Find the app that owns these credentials"
echo "  4. DELETE or REVOKE the old credentials"
echo "  5. CREATE NEW credentials (new Consumer Key/Secret)"
echo "  6. Copy the new values to your LOCAL .env (never commit!)"
echo ""

read -p "Have you revoked the old credentials and created new ones? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Please complete credential rotation on Daraja before continuing."
    exit 1
fi

# Step 3: Update local .env
echo ""
echo "💾 Step 3: Update your local .env"
echo "=================================="
echo ""
echo "Edit ~/.env with your NEW credentials (do NOT commit this file):"
echo ""
echo "  MPESA_CONSUMER_KEY=<NEW_KEY>"
echo "  MPESA_CONSUMER_SECRET=<NEW_SECRET>"
echo "  MPESA_PASSKEY=<NEW_PASSKEY>"
echo ""

read -p "Press enter after updating .env with new credentials..."

# Step 4: Verify .env is gitignored
echo ""
echo "✅ Verifying .env is in .gitignore..."
if grep -q "^\.env\$" .gitignore; then
    echo "   ✓ .env is in .gitignore"
else
    echo "   ✗ .env NOT in .gitignore - adding it now"
    echo ".env" >> .gitignore
    git add .gitignore
    git commit -m "chore: ensure .env is gitignored (security)"
fi

# Step 5: Remove hardcoded credentials from mpesa_test.py
echo ""
echo "🧹 Step 5: Remove hardcoded credentials from mpesa_test.py"
echo "=========================================="
cat > mpesa_test.py << 'EOF'
import base64
import requests
import time
import os
from dotenv import load_dotenv

# Load credentials from .env (never hardcode!)
load_dotenv()

MPESA_CONSUMER_KEY = os.getenv("MPESA_CONSUMER_KEY")
MPESA_CONSUMER_SECRET = os.getenv("MPESA_CONSUMER_SECRET")

if not MPESA_CONSUMER_KEY or not MPESA_CONSUMER_SECRET:
    raise ValueError("MPESA_CONSUMER_KEY and MPESA_CONSUMER_SECRET must be set in .env")

OAUTH_URL = "https://sandbox.safaricom.co.ke/oauth/v1/generate?grant_type=client_credentials"

# Encode key:secret to Base64
key_secret = f"{MPESA_CONSUMER_KEY}:{MPESA_CONSUMER_SECRET}"
auth_header = base64.b64encode(key_secret.encode()).decode()
headers = {"Authorization": f"Basic {auth_header}"}

max_attempts = 5
delay_seconds = 5

for attempt in range(1, max_attempts + 1):
    try:
        response = requests.get(OAUTH_URL, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()
        print("✅ Access token retrieved successfully!")
        print("Access Token:", data.get("access_token"))
        print("Expires in:", data.get("expires_in"))
        break  # success, exit loop
    except requests.exceptions.HTTPError as http_err:
        print(f"❌ Attempt {attempt} HTTP error: {http_err}")
        if response is not None:
            try:
                error_detail = response.json()
                print(f"   Details: {error_detail}")
            except Exception:
                print(f"   Response: {response.text}")
        if attempt < max_attempts:
            print(f"   Retrying in {delay_seconds} seconds...")
            time.sleep(delay_seconds)
    except requests.exceptions.RequestException as req_err:
        print(f"❌ Attempt {attempt} Request error: {req_err}")
        if attempt < max_attempts:
            print(f"   Retrying in {delay_seconds} seconds...")
            time.sleep(delay_seconds)

print("\n✓ Test complete")
EOF

echo "   ✓ mpesa_test.py updated to use .env instead of hardcoded values"
git add mpesa_test.py
git commit -m "security: load MPESA credentials from .env instead of hardcoding"

echo ""
echo "✅ REMEDIATION COMPLETE"
echo "======================="
echo ""
echo "NEXT STEPS:"
echo "  1. Clean git history of .env (see Step 1 above)"
echo "  2. Force push to GitHub"
echo "  3. Add SECURITY.md to your repo with incident response guidelines"
echo "  4. Consider enabling branch protection rules"
echo ""
echo "Your new credentials are safe in local .env (gitignored)."
echo ""
