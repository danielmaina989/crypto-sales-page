#!/bin/bash
# 🚀 Crypto Sales Page - One-Time Setup Script
# This script sets up the entire project for first-time use

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
log_info() {
    echo -e "${BLUE}ℹ️  $1${NC}"
}

log_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

log_warning() {
    echo -e "${YELLOW}⚠️  $1${NC}"
}

log_error() {
    echo -e "${RED}❌ $1${NC}"
}

log_section() {
    echo ""
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
    echo -e "${BLUE}$1${NC}"
    echo -e "${BLUE}═══════════════════════════════════════════════════════════${NC}"
}

# STEP 1: Check Python and virtualenv
log_section "STEP 1: Checking Python Environment"

if command -v python3 &> /dev/null; then
    PYTHON_VERSION=$(python3 --version)
    log_success "Python found: $PYTHON_VERSION"
else
    log_error "Python3 not found. Please install Python 3.10 or higher."
    exit 1
fi

# STEP 2: Activate virtualenv
log_section "STEP 2: Setting Up Virtual Environment"

if [ -d "crypto/bin" ]; then
    log_info "Virtual environment found at ./crypto"
    source crypto/bin/activate
    log_success "Virtual environment activated"
else
    log_warning "Virtual environment not found. Creating one..."
    python3 -m venv crypto
    source crypto/bin/activate
    log_success "Virtual environment created and activated"
fi

# Verify we're in the virtualenv
if [[ "$VIRTUAL_ENV" == "" ]]; then
    log_error "Failed to activate virtual environment"
    exit 1
fi
log_success "Running in virtualenv: $VIRTUAL_ENV"

# STEP 3: Upgrade pip
log_section "STEP 3: Upgrading pip"

pip install --upgrade pip setuptools wheel > /dev/null 2>&1
log_success "pip upgraded"

# STEP 4: Install dependencies
log_section "STEP 4: Installing Python Dependencies"

if [ -f "requirements.txt" ]; then
    log_info "Installing from requirements.txt..."
    pip install -r requirements.txt
    log_success "Dependencies installed"
else
    log_warning "requirements.txt not found, installing Django manually..."
    pip install django djangorestframework django-cors-headers python-dotenv celery redis requests
    log_success "Core dependencies installed"
fi

# STEP 5: Create .env from template
log_section "STEP 5: Setting Up Environment Variables"

if [ -f ".env" ]; then
    log_warning ".env already exists. Skipping creation."
    log_info "If you need to reset, run: cp .env.example .env"
else
    if [ -f ".env.example" ]; then
        cp .env.example .env
        log_success ".env created from .env.example"
        log_warning "⚠️  IMPORTANT: Edit .env with your actual credentials:"
        log_warning "   - MPESA_CONSUMER_KEY"
        log_warning "   - MPESA_CONSUMER_SECRET"
        log_warning "   - MPESA_PASSKEY"
        log_warning "   - MPESA_CALLBACK_URL (your ngrok URL or domain)"
    else
        log_error ".env.example not found"
        exit 1
    fi
fi

# STEP 6: Check Django settings
log_section "STEP 6: Verifying Django Configuration"

export DJANGO_SETTINGS_MODULE=core.settings

# Test Django import
python -c "import django; django.setup()" 2>&1 | grep -i "error" && {
    log_error "Django configuration error"
    exit 1
} || log_success "Django configuration valid"

# STEP 7: Run database migrations
log_section "STEP 7: Setting Up Database"

log_info "Running migrations..."
python manage.py migrate --noinput
log_success "Migrations completed"

# STEP 8: Collect static files
log_section "STEP 8: Collecting Static Files"

python manage.py collectstatic --noinput
log_success "Static files collected"

# STEP 9: Create superuser (optional)
log_section "STEP 9: Creating Admin User (Optional)"

read -p "Create a Django superuser now? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    python manage.py createsuperuser
    log_success "Superuser created"
else
    log_info "Skipped superuser creation. You can create one later with:"
    log_info "  python manage.py createsuperuser"
fi

# STEP 10: Check Celery and Redis
log_section "STEP 10: Checking Celery & Redis (Optional, for background tasks)"

# Check Celery
if python -c "import celery" 2>/dev/null; then
    log_success "Celery: installed"
else
    log_warning "Celery: not found in requirements"
fi

# Check Redis
if command -v redis-cli &> /dev/null; then
    log_info "Redis found on system"
    if redis-cli ping &> /dev/null; then
        log_success "Redis is running and responding"
    else
        log_warning "Redis is installed but not currently running"
        log_info "Start Redis with: redis-server"
    fi
else
    log_warning "Redis not installed. For Celery to work, you'll need Redis:"
    log_warning "  Ubuntu/Debian: sudo apt-get install redis-server"
    log_warning "  macOS: brew install redis"
    log_warning "  Or use docker: docker run -d -p 6379:6379 redis:latest"
fi

# STEP 11: Display summary and next steps
log_section "✨ SETUP COMPLETE!"

echo ""
echo -e "${GREEN}Your project is ready to run!${NC}"
echo ""
echo "📋 NEXT STEPS:"
echo ""
echo "1️⃣  Edit .env with your credentials:"
echo "   nano .env"
echo "   (or use your favorite editor)"
echo ""
echo "2️⃣  Start all services with our dev script:"
echo "   ./dev.sh"
echo "   (choose option 4 for 'All services' or 6 for 'Django + Celery')"
echo ""
echo "   OR start them manually:"
echo ""
echo "   Terminal 1 - Django dev server:"
echo "   python manage.py runserver"
echo ""
echo "   Terminal 2 - Redis (if using Celery):"
echo "   redis-server"
echo ""
echo "   Terminal 3 - Celery worker:"
echo "   celery -A core.celery worker -l info"
echo ""
echo "3️⃣  Access the app:"
echo "   🌐 Admin: http://127.0.0.1:8000/admin/"
echo "   🌐 App: http://127.0.0.1:8000/"
echo ""
echo "📚 Documentation:"
echo "   - README.md - Project overview"
echo "   - SECURITY.md - Security best practices"
echo "   - CREDENTIALS_BREACH_REMEDIATION.md - If credentials are exposed"
echo ""
echo "🔐 IMPORTANT REMINDERS:"
echo "   ✓ Never commit .env to git (it's in .gitignore)"
echo "   ✓ Keep credentials.example.json, not credentials.json"
echo "   ✓ Rotate MPESA sandbox credentials regularly"
echo "   ✓ Always use HTTPS in production (DEBUG=False)"
echo ""
log_success "Setup script completed successfully!"
echo ""
