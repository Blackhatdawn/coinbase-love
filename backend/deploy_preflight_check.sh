#!/bin/bash
# Production Deployment Helper Script
# This script validates the backend configuration and prepares for deployment

set -e

echo ""
echo "╔════════════════════════════════════════════════════════════════╗"
echo "║   CryptoVault Backend - Production Deployment Helper          ║"
echo "║   Version 1.0.0                                               ║"
echo "╚════════════════════════════════════════════════════════════════╝"
echo ""

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check functions
check_env_var() {
    local var_name=$1
    local var_value=${!var_name}
    
    if [ -z "$var_value" ]; then
        echo -e "${RED}❌${NC} ${var_name} is not set"
        return 1
    else
        # Mask sensitive values
        if [[ "$var_name" == *"SECRET"* ]] || [[ "$var_name" == *"PASSWORD"* ]] || [[ "$var_name" == *"TOKEN"* ]] || [[ "$var_name" == *"KEY"* ]]; then
            echo -e "${GREEN}✅${NC} ${var_name} is set (value masked for security)"
        else
            echo -e "${GREEN}✅${NC} ${var_name} = ${var_value:0:50}..."
        fi
        return 0
    fi
}

check_python_packages() {
    echo ""
    echo "📦 Checking Python packages..."
    
    local required_packages=("fastapi" "uvicorn" "motor" "pydantic" "python-dotenv")
    local missing_packages=()
    
    for package in "${required_packages[@]}"; do
        if python3 -c "import ${package//-/_}" 2>/dev/null; then
            echo -e "  ${GREEN}✅${NC} ${package}"
        else
            echo -e "  ${RED}❌${NC} ${package} (missing)"
            missing_packages+=("$package")
        fi
    done
    
    if [ ${#missing_packages[@]} -gt 0 ]; then
        echo ""
        echo -e "${YELLOW}⚠️ Missing packages:${NC} ${missing_packages[@]}"
        echo "Run: pip install -r requirements.txt"
        return 1
    fi
    
    return 0
}

check_mongodb() {
    echo ""
    echo "🗄️ Checking MongoDB configuration..."
    
    if [ -z "$MONGO_URL" ]; then
        echo -e "${RED}❌${NC} MONGO_URL not set"
        return 1
    fi
    
    echo -e "${GREEN}✅${NC} MONGO_URL is configured"
    
    # Try to ping MongoDB (requires mongocli or mongo shell)
    if command -v mongosh &> /dev/null; then
        echo -n "  Attempting connection... "
        if timeout 5 mongosh "$MONGO_URL" --eval "db.adminCommand('ping')" &>/dev/null; then
            echo -e "${GREEN}Connected${NC}"
        else
            echo -e "${YELLOW}Could not verify${NC} (install mongosh to test)"
        fi
    else
        echo -e "${YELLOW}⚠️${NC} mongosh not installed (skipping connectivity test)"
    fi
    
    return 0
}

check_critical_env_vars() {
    echo ""
    echo "🔐 Checking critical environment variables..."
    
    local critical_vars=(
        "PORT"
        "HOST"
        "ENVIRONMENT"
        "MONGO_URL"
        "DB_NAME"
        "JWT_SECRET"
        "CSRF_SECRET"
        "APP_URL"
        "CORS_ORIGINS"
    )
    
    local missing=0
    for var in "${critical_vars[@]}"; do
        if ! check_env_var "$var"; then
            missing=$((missing + 1))
        fi
    done
    
    if [ $missing -gt 0 ]; then
        echo ""
        echo -e "${RED}❌ Missing $missing critical environment variables${NC}"
        return 1
    fi
    
    return 0
}

check_email_config() {
    echo ""
    echo "📧 Checking email configuration..."
    
    if [ -z "$EMAIL_SERVICE" ]; then
        echo -e "${YELLOW}⚠️${NC} EMAIL_SERVICE not set (defaulting to sendgrid)"
        EMAIL_SERVICE="sendgrid"
    fi
    
    case "$EMAIL_SERVICE" in
        smtp)
            check_env_var "SMTP_HOST" || return 1
            check_env_var "SMTP_PORT" || return 1
            check_env_var "SMTP_USERNAME" || return 1
            check_env_var "SMTP_PASSWORD" || return 1
            ;;
        sendgrid)
            check_env_var "SENDGRID_API_KEY" || return 1
            ;;
        resend)
            check_env_var "RESEND_API_KEY" || return 1
            ;;
        mock)
            echo -e "${YELLOW}⚠️${NC} Using mock email service (development only)"
            ;;
    esac
    
    return 0
}

validate_urls() {
    echo ""
    echo "🌐 Validating URLs..."
    
    local urls=(
        "APP_URL"
        "PUBLIC_API_URL"
        "PUBLIC_WS_URL"
    )
    
    for url_var in "${urls[@]}"; do
        local url_value=${!url_var}
        
        if [ -z "$url_value" ]; then
            echo -e "${YELLOW}⚠️${NC} ${url_var} not set"
            continue
        fi
        
        # Basic URL validation
        if [[ $url_value =~ ^https?:// ]] || [[ $url_value =~ ^wss?:// ]]; then
            echo -e "${GREEN}✅${NC} ${url_var} format valid"
        else
            echo -e "${RED}❌${NC} ${url_var} must start with http://, https://, ws://, or wss://"
            return 1
        fi
    done
    
    return 0
}

check_ports() {
    echo ""
    echo "🔌 Checking port availability..."
    
    local port=$PORT
    if [ -z "$port" ]; then
        port=8000
    fi
    
    if command -v lsof &> /dev/null; then
        if lsof -i :$port &>/dev/null; then
            echo -e "${RED}❌${NC} Port $port is already in use"
            echo "  Processes using port $port:"
            lsof -i :$port
            return 1
        else
            echo -e "${GREEN}✅${NC} Port $port is available"
        fi
    else
        echo -e "${YELLOW}⚠️${NC} lsof not available (skipping port check)"
    fi
    
    return 0
}

show_summary() {
    local passed=$1
    local failed=$2
    local warnings=$3
    
    echo ""
    echo "╔════════════════════════════════════════════════════════════════╗"
    echo "║                    Deployment Checklist                        ║"
    echo "╚════════════════════════════════════════════════════════════════╝"
    echo ""
    
    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}✅ All critical checks passed!${NC}"
        if [ $warnings -gt 0 ]; then
            echo -e "${YELLOW}⚠️  $warnings warnings (non-critical)${NC}"
        fi
        echo ""
        echo "Ready to deploy! Use:"
        echo "  ./start_production.sh"
        echo ""
        return 0
    else
        echo -e "${RED}❌ $failed critical check(s) failed${NC}"
        echo -e "${YELLOW}⚠️  $warnings warning(s)${NC}"
        echo ""
        echo "Please fix the above issues and run the script again."
        echo ""
        return 1
    fi
}

# Main execution
main() {
    local failed=0
    local warnings=0
    
    # Load .env file if it exists
    if [ -f ".env" ]; then
        echo "📄 Loading environment from .env file..."
        set -a
        source .env
        set +a
        echo ""
    else
        echo -e "${YELLOW}⚠️${NC} .env file not found (using system environment variables)"
        echo ""
    fi
    
    # Run checks
    check_critical_env_vars || failed=$((failed + 1))
    check_python_packages || failed=$((failed + 1))
    check_email_config || failed=$((failed + 1))
    validate_urls || failed=$((failed + 1))
    check_ports || failed=$((failed + 1))
    check_mongodb || warnings=$((warnings + 1))
    
    # Show summary
    show_summary $failed $warnings $warnings
    exit $failed
}

# Run main function
main "$@"