#!/bin/bash

###############################################################################
# SUPPORT STARTER AI - AUTO DEPLOY SCRIPT
# ========================================
# One-click deployment to Railway, Render or Fly.io
#
# Usage:
#   ./deploy.sh railway    # Deploy to Railway
#   ./deploy.sh render     # Deploy to Render
#   ./deploy.sh fly        # Deploy to Fly.io
###############################################################################

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

print_header() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════╗"
    echo "║                                                          ║"
    echo "║         SUPPORT STARTER AI - AUTO DEPLOY                ║"
    echo "║         Version 2.0.0                                    ║"
    echo "║                                                          ║"
    echo "╚══════════════════════════════════════════════════════════╝"
    echo ""
}

# Check dependencies
check_dependencies() {
    print_info "Checking dependencies..."

    if ! command -v git &> /dev/null; then
        print_error "git is not installed. Please install git first."
        exit 1
    fi

    if ! command -v node &> /dev/null; then
        print_warning "node.js is not installed. Some features may not work."
    fi

    print_success "Dependencies OK"
}

# Check if Railway CLI is installed
check_railway() {
    if ! command -v railway &> /dev/null; then
        print_info "Installing Railway CLI..."
        npm install -g @railway/cli || {
            print_error "Failed to install Railway CLI. Please install manually: npm install -g @railway/cli"
            exit 1
        }
    fi
    print_success "Railway CLI ready"
}

# Check if Render CLI is installed
check_render() {
    if ! command -v render &> /dev/null; then
        print_warning "Render CLI not found. Please deploy via web interface at https://render.com"
        print_info "Opening browser..."
        if command -v open &> /dev/null; then
            open "https://dashboard.render.com/select-repo?type=web"
        elif command -v xdg-open &> /dev/null; then
            xdg-open "https://dashboard.render.com/select-repo?type=web"
        fi
        return 1
    fi
    print_success "Render CLI ready"
    return 0
}

# Check if Fly CLI is installed
check_fly() {
    if ! command -v flyctl &> /dev/null; then
        print_info "Installing Fly.io CLI..."
        curl -L https://fly.io/install.sh | sh || {
            print_error "Failed to install Fly.io CLI. Please install manually."
            exit 1
        }
        # Add to PATH if needed
        export PATH="$HOME/.fly/bin:$PATH"
    fi
    print_success "Fly.io CLI ready"
}

# Deploy to Railway
deploy_railway() {
    print_header
    print_info "Deploying to Railway..."

    check_dependencies
    check_railway

    # Check if logged in
    if ! railway whoami &> /dev/null; then
        print_info "Please login to Railway..."
        railway login
    fi

    # Initialize or link project
    if [ ! -f "railway.json" ]; then
        print_info "Initializing Railway project..."
        railway init
    else
        print_info "Using existing Railway project"
        railway link
    fi

    # Add environment variables
    print_info "Setting up environment variables..."
    echo ""
    print_warning "Please enter your Anthropic API Key (or press ENTER to skip):"
    read -r API_KEY
    if [ -n "$API_KEY" ]; then
        railway variables set ANTHROPIC_API_KEY="$API_KEY"
    fi

    # Deploy
    print_info "Deploying to Railway..."
    railway up

    # Get the deployed URL
    DOMAIN=$(railway domain | head -n 1 | awk '{print $1}')
    print_success "Deployed to: https://$DOMAIN"
    print_info "Setup wizard: https://$DOMAIN/setup"
    print_info "Admin panel: https://$DOMAIN/admin"
}

# Deploy to Render
deploy_render() {
    print_header
    print_info "Deploying to Render..."

    check_dependencies

    if ! check_render; then
        return 1
    fi

    # Create render.yaml if not exists
    if [ ! -f "render.yaml" ]; then
        print_info "Creating render.yaml..."
        cat > render.yaml << 'EOF'
services:
  - type: web
    name: support-starter-bot
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: uvicorn server:app --host 0.0.0.0 --port $PORT
    envVars:
      - key: PYTHON_VERSION
        value: 3.11
      - key: PORT
        value: 8000
EOF
    fi

    print_info "Deploying via Render CLI..."
    render deploy

    print_success "Deployed to Render!"
    print_info "Check your dashboard at https://dashboard.render.com"
}

# Deploy to Fly.io
deploy_fly() {
    print_header
    print_info "Deploying to Fly.io..."

    check_dependencies
    check_fly

    # Check if logged in
    if ! flyctl auth whoami &> /dev/null; then
        print_info "Please login to Fly.io..."
        flyctl auth login
    fi

    # Create fly.toml if not exists
    if [ ! -f "fly.toml" ]; then
        print_info "Creating fly.toml..."
        cat > fly.toml << 'EOF'
app = "support-starter-bot"
primary_region = "arn"

[build]
  [build.buildpacks]
    builder = "heroku/buildpacks:20"

[env]
  PORT = "8000"

[[services]]
  protocol = "tcp"
  internal_port = 8000

  [[services.ports]]
    port = 80
    handlers = ["http"]

  [[services.ports]]
    port = 443
    handlers = ["tls", "http"]

[deploy]
  strategy = "immediate"
EOF
    fi

    # Deploy
    print_info "Deploying to Fly.io..."
    flyctl deploy

    # Get the deployed URL
    APP_NAME=$(grep '^app = ' fly.toml | sed 's/app = "\(.*\)"/\1/')
    print_success "Deployed to: https://$APP_NAME.fly.dev"
    print_info "Setup wizard: https://$APP_NAME.fly.dev/setup"
    print_info "Admin panel: https://$APP_NAME.fly.dev/admin"
}

# Main deployment logic
main() {
    print_header

    # Determine deployment target
    if [ -z "$1" ]; then
        echo "Select deployment target:"
        echo "  1) Railway (Recommended - Free tier available)"
        echo "  2) Render (Good free tier)"
        echo "  3) Fly.io (Fast deployment)"
        echo ""
        read -p "Enter choice [1-3]: " choice
        case $choice in
            1) PLATFORM="railway" ;;
            2) PLATFORM="render" ;;
            3) PLATFORM="fly" ;;
            *) print_error "Invalid choice"; exit 1 ;;
        esac
    else
        PLATFORM="$1"
    fi

    # Deploy to selected platform
    case "$PLATFORM" in
        railway)
            deploy_railway
            ;;
        render)
            deploy_render
            ;;
        fly)
            deploy_fly
            ;;
        *)
            print_error "Unknown platform: $PLATFORM"
            echo "Usage: $0 [railway|render|fly]"
            exit 1
            ;;
    esac

    print_success "Deployment complete!"
}

# Run main function
main "$@"
