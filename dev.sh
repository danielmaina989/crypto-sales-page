#!/bin/bash
# 🚀 Start Development Environment - Runs all necessary services

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

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

# Check if .env exists
if [ ! -f ".env" ]; then
    log_error ".env file not found"
    log_info "Run ./setup.sh first to initialize the project"
    exit 1
fi

# Activate virtualenv
if [ ! -d "crypto/bin" ]; then
    log_error "Virtual environment not found"
    log_info "Run ./setup.sh to set up the project"
    exit 1
fi

source crypto/bin/activate

log_section "🚀 CRYPTO SALES PAGE - Development Environment"

echo ""
echo "Available services:"
echo "  1) Django dev server (http://127.0.0.1:8000)"
echo "  2) Redis server"
echo "  3) Celery worker"
echo "  4) All services (opens multiple terminals)"
echo "  5) Django + Celery (grouped logging)"
echo "  6) Environment check"
echo ""

read -p "Choose option (1-6): " choice

case $choice in
    1)
        log_section "Starting Django Development Server"
        log_warning "Press Ctrl+C to stop"
        echo ""
        python manage.py runserver 0.0.0.0:8000
        ;;
    2)
        log_section "Starting Redis Server"
        log_warning "Press Ctrl+C to stop"
        echo ""
        if command -v redis-server &> /dev/null; then
            redis-server
        else
            log_error "Redis not installed"
            log_info "Install with: sudo apt-get install redis-server (Linux) or brew install redis (macOS)"
            exit 1
        fi
        ;;
    3)
        log_section "Starting Celery Worker"
        log_warning "Press Ctrl+C to stop"
        echo ""
        export CELERY_BROKER_URL=redis://localhost:6379/0
        export CELERY_RESULT_BACKEND=$CELERY_BROKER_URL
        celery -A core.celery worker -l info
        ;;
    4)
        log_section "Starting All Services"
        log_warning "Multiple terminals will open. Close them individually to stop services."
        echo ""
        
        # Check if running on macOS or Linux
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            log_info "Opening terminals (macOS)..."
            
            # Start Redis
            open -a Terminal <<EOF
cd "$(pwd)" && redis-server
EOF
            sleep 1
            
            # Start Django
            open -a Terminal <<EOF
cd "$(pwd)" && source crypto/bin/activate && python manage.py runserver
EOF
            sleep 1
            
            # Start Celery
            open -a Terminal <<EOF
cd "$(pwd)" && source crypto/bin/activate && export CELERY_BROKER_URL=redis://localhost:6379/0 && celery -A core.celery worker -l info
EOF
            
            log_success "All services started in separate terminals!"
            log_info "Django: http://127.0.0.1:8000"
            log_info "Admin: http://127.0.0.1:8000/admin"
            
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            log_info "Opening terminals (Linux with x-terminal-emulator)..."
            
            if command -v x-terminal-emulator &> /dev/null; then
                # Start Redis
                x-terminal-emulator -e bash -c "cd $(pwd) && redis-server; bash" &
                sleep 1
                
                # Start Django
                x-terminal-emulator -e bash -c "cd $(pwd) && source crypto/bin/activate && python manage.py runserver; bash" &
                sleep 1
                
                # Start Celery
                x-terminal-emulator -e bash -c "cd $(pwd) && source crypto/bin/activate && export CELERY_BROKER_URL=redis://localhost:6379/0 && celery -A core.celery worker -l info; bash" &
                
                log_success "All services started in separate terminals!"
                log_info "Django: http://127.0.0.1:8000"
                log_info "Admin: http://127.0.0.1:8000/admin"
            else
                log_warning "No terminal emulator found. Please start services manually in separate terminals:"
                echo ""
                echo "Terminal 1 - Redis:"
                echo "  redis-server"
                echo ""
                echo "Terminal 2 - Django:"
                echo "  source crypto/bin/activate"
                echo "  python manage.py runserver"
                echo ""
                echo "Terminal 3 - Celery:"
                echo "  source crypto/bin/activate"
                echo "  export CELERY_BROKER_URL=redis://localhost:6379/0"
                echo "  celery -A core.celery worker -l info"
            fi
        else
            log_error "Unsupported OS. Please start services manually."
        fi
        ;;
    5)
        log_section "Starting Django + Celery"
        log_warning "Press Ctrl+C to stop. Both services will run with grouped logging."
        echo ""
        
        # Check if running on macOS or Linux
        if [[ "$OSTYPE" == "darwin"* ]]; then
            # macOS
            log_info "Opening terminals (macOS)..."
            
            # Start Django
            open -a Terminal <<EOF
cd "$(pwd)" && source crypto/bin/activate && python manage.py runserver
EOF
            sleep 1
            
            # Start Celery
            open -a Terminal <<EOF
cd "$(pwd)" && source crypto/bin/activate && export CELERY_BROKER_URL=redis://localhost:6379/0 && celery -A core.celery worker -l info
EOF
            
            log_success "Django + Celery started in separate terminals!"
            log_info "Django: http://127.0.0.1:8000"
            log_info "Admin: http://127.0.0.1:8000/admin"
            log_warning "Note: Make sure Redis is running in another terminal!"
            
        elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
            # Linux
            log_info "Opening terminals (Linux)..."
            
            if command -v x-terminal-emulator &> /dev/null; then
                # Start Django
                x-terminal-emulator -e bash -c "cd $(pwd) && source crypto/bin/activate && python manage.py runserver; bash" &
                sleep 1
                
                # Start Celery
                x-terminal-emulator -e bash -c "cd $(pwd) && source crypto/bin/activate && export CELERY_BROKER_URL=redis://localhost:6379/0 && celery -A core.celery worker -l info; bash" &
                
                log_success "Django + Celery started in separate terminals!"
                log_info "Django: http://127.0.0.1:8000"
                log_info "Admin: http://127.0.0.1:8000/admin"
                log_warning "Note: Make sure Redis is running in another terminal!"
            else
                log_warning "No terminal emulator found. Please start in separate terminals:"
                echo ""
                echo "Terminal 1 - Django:"
                echo "  source crypto/bin/activate"
                echo "  python manage.py runserver"
                echo ""
                echo "Terminal 2 - Celery:"
                echo "  source crypto/bin/activate"
                echo "  export CELERY_BROKER_URL=redis://localhost:6379/0"
                echo "  celery -A core.celery worker -l info"
            fi
        else
            log_error "Unsupported OS. Please start services manually."
        fi
        ;;
    6)
        log_section "Environment Check"
        echo ""
        
        # Check Python
        python_version=$(python --version 2>&1)
        log_success "Python: $python_version"
        
        # Check Django
        django_version=$(python -c "import django; print(django.VERSION[0])" 2>/dev/null)
        log_success "Django: installed"
        
        # Check .env
        if [ -f ".env" ]; then
            log_success ".env: exists"
        else
            log_warning ".env: not found"
        fi
        
        # Check Redis
        if command -v redis-cli &> /dev/null; then
            if redis-cli ping &> /dev/null; then
                log_success "Redis: running"
            else
                log_warning "Redis: installed but not running"
            fi
        else
            log_warning "Redis: not installed"
        fi
        
        # Check Celery
        if python -c "import celery" 2>/dev/null; then
            log_success "Celery: installed"
        else
            log_warning "Celery: not installed"
        fi
        
        # Check migrations
        unapplied=$(python manage.py showmigrations --list 2>/dev/null | grep "\[ \]" | wc -l)
        if [ "$unapplied" -eq 0 ]; then
            log_success "Database migrations: all applied"
        else
            log_warning "Database migrations: $unapplied unapplied"
        fi
        
        echo ""
        log_success "Environment check complete!"
        ;;
    *)
        log_error "Invalid option"
        exit 1
        ;;
esac
