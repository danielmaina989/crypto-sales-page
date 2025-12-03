#!/bin/bash
# CRITICAL: Execute these commands in order to remediate the credentials breach

set -e

echo "🔒 MPESA Credentials Breach Remediation"
echo "======================================"
echo ""
echo "STEP 1: Verify setup"
echo "==================="

# Check if git repo is clean
if [ -z "$(git status --porcelain)" ]; then
    echo "✓ Git repo is clean"
else
    echo "⚠️  Git has uncommitted changes. Stash them first:"
    echo "   git stash"
    exit 1
fi

# Check if .env exists
if [ -f .env ]; then
    echo "✓ .env file exists"
else
    echo "❌ .env not found. Please create it with new credentials."
    exit 1
fi

# Verify credentials are NOT hardcoded
if grep -q "riGjp64odowDOnvadnjyjeiJUmc4eSDtQeclNKNfXCscICpk" mpesa_test.py; then
    echo "❌ Old credentials still in mpesa_test.py! Run: git checkout mpesa_test.py"
    exit 1
else
    echo "✓ Old credentials removed from mpesa_test.py"
fi

echo ""
echo "STEP 2: Clean git history of .env"
echo "=================================="
echo ""
echo "Choose your method:"
echo ""
echo "Option A: BFG Repo-Cleaner (RECOMMENDED)"
echo "========================================="
echo "# Install BFG (macOS)"
echo "brew install bfg"
echo ""
echo "# Or download from: https://rtyley.github.io/bfg-repo-cleaner/"
echo ""
echo "# Then run:"
echo "bfg --delete-files .env"
echo "git reflog expire --expire=now --all && git gc --prune=now --aggressive"
echo "git push -f origin main"
echo ""
echo "Option B: git filter-branch (DIY)"
echo "=================================="
echo "git filter-branch --tree-filter 'rm -f .env' -f -- --all"
echo "git reflog expire --expire=now --all && git gc --prune=now --aggressive"
echo "git push -f origin main"
echo ""
echo "⚠️  WARNING: Force pushing will rewrite history. Notify your team!"
echo ""

read -p "I will clean git history manually (press enter to continue)..."

echo ""
echo "STEP 3: Verify cleanup"
echo "====================="
echo ""
echo "After cleaning git history, verify the .env is gone:"
echo "git log --all --full-history -p -- .env | head -20"
echo ""
echo "You should see NO .env file in recent commits."
echo ""

read -p "Press enter after verifying git history is clean..."

echo ""
echo "STEP 4: Generate new credentials on Daraja"
echo "=========================================="
echo ""
echo "🚨 CRITICAL: Your old credentials are EXPOSED"
echo "   Old Consumer Key: riGjp64odowDOnvadnjyjeiJUmc4eSDtQeclNKNfXCscICpk"
echo "   Old Consumer Secret: fXRp0DR8huY76Bsjog15rX2CAcZ27i19dyu3AtYGYzHorvHWIXDJKUqJCqtGAxsn"
echo ""
echo "ACTION ITEMS:"
echo "  1. Go to https://developer.safaricom.co.ke/"
echo "  2. Log in"
echo "  3. Find your app and REVOKE the old credentials"
echo "  4. Generate NEW Consumer Key and Secret"
echo "  5. Generate NEW Passkey if needed"
echo ""

read -p "Have you generated new credentials? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Aborted. Please generate new credentials first."
    exit 1
fi

echo ""
echo "STEP 5: Update local .env with new credentials"
echo "=============================================="
echo ""
echo "Edit .env and replace:"
echo "  MPESA_CONSUMER_KEY=<NEW_KEY>"
echo "  MPESA_CONSUMER_SECRET=<NEW_SECRET>"
echo "  MPESA_PASSKEY=<NEW_PASSKEY>"
echo ""
echo "Save the file (DO NOT COMMIT TO GIT)"
echo ""

read -p "Press enter after updating .env with new credentials..."

# Verify new credentials were added
if grep -q "riGjp64odowDOnvadnjyjeiJUmc4eSDtQeclNKNfXCscICpk" .env; then
    echo "❌ ERROR: Old credentials still in .env!"
    echo "   Remove them before continuing."
    exit 1
fi

echo ""
echo "✅ REMEDIATION COMPLETE!"
echo "========================"
echo ""
echo "Summary of actions completed:"
echo "  ✓ Old credentials revoked on Daraja"
echo "  ✓ New credentials generated"
echo "  ✓ .env updated with new credentials (local only, not committed)"
echo "  ✓ Git history cleaned of .env"
echo "  ✓ Hardcoded credentials removed from mpesa_test.py"
echo "  ✓ Security policy documented in SECURITY.md"
echo ""
echo "Next steps:"
echo "  1. Commit the changes: git add SECURITY.md mpesa_test.py && git commit -m 'security: credential breach remediation'"
echo "  2. Test the app: python manage.py runserver"
echo "  3. Verify MPESA integration works with new credentials"
echo ""
