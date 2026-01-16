#!/bin/bash
# Penny Stock Picker - CloudPanel Deployment Script
# Run this script on your CloudPanel server

set -e

# Configuration
DOMAIN="penny.co-l.in"
APP_DIR="/home/penny/htdocs/${DOMAIN}"
BACKEND_DIR="${APP_DIR}/backend"
FRONTEND_DIR="${APP_DIR}/frontend"
LOG_DIR="/var/log/penny"
PYTHON_VERSION="3.12"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo_error "Please run as root (sudo)"
    exit 1
fi

echo_info "Starting Penny Stock Picker deployment..."

# Create log directory
echo_info "Creating log directory..."
mkdir -p ${LOG_DIR}
chown penny:penny ${LOG_DIR}

# Install system dependencies
echo_info "Installing system dependencies..."
apt-get update
apt-get install -y \
    python${PYTHON_VERSION} \
    python${PYTHON_VERSION}-venv \
    python${PYTHON_VERSION}-dev \
    build-essential \
    libpq-dev \
    redis-server \
    curl

# Install Node.js 20 LTS if not present
if ! command -v node &> /dev/null || [[ $(node -v) != v20* ]]; then
    echo_info "Installing Node.js 20 LTS..."
    curl -fsSL https://deb.nodesource.com/setup_20.x | bash -
    apt-get install -y nodejs
fi

# Enable and start Redis
echo_info "Configuring Redis..."
systemctl enable redis-server
systemctl start redis-server

# Check if PostgreSQL is installed via CloudPanel
if ! command -v psql &> /dev/null; then
    echo_error "PostgreSQL not found. Please ensure PostgreSQL is installed via CloudPanel."
    exit 1
fi

# Install TimescaleDB if not already installed
if ! dpkg -l | grep -q timescaledb; then
    echo_info "Installing TimescaleDB..."
    apt-get install -y gnupg postgresql-common apt-transport-https lsb-release wget
    echo "deb https://packagecloud.io/timescale/timescaledb/ubuntu/ $(lsb_release -c -s) main" | tee /etc/apt/sources.list.d/timescaledb.list
    wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | apt-key add -
    apt-get update
    apt-get install -y timescaledb-2-postgresql-14
    timescaledb-tune --quiet --yes
    systemctl restart postgresql
fi

# Check if application directory exists
if [ ! -d "${APP_DIR}" ]; then
    echo_error "Application directory not found: ${APP_DIR}"
    echo_info "Please create a site in CloudPanel first for domain: ${DOMAIN}"
    exit 1
fi

# Setup Python virtual environment
echo_info "Setting up Python virtual environment..."
cd ${BACKEND_DIR}

if [ ! -d "venv" ]; then
    python${PYTHON_VERSION} -m venv venv
fi

source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

chown -R penny:penny ${BACKEND_DIR}/venv

# Build frontend
echo_info "Building frontend..."
cd ${FRONTEND_DIR}

if [ -d "node_modules" ]; then
    rm -rf node_modules
fi

npm install
npm run build

chown -R penny:penny ${FRONTEND_DIR}

# Copy systemd service files
echo_info "Installing systemd services..."
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cp ${SCRIPT_DIR}/penny-api.service /etc/systemd/system/
cp ${SCRIPT_DIR}/penny-celery.service /etc/systemd/system/
cp ${SCRIPT_DIR}/penny-celery-beat.service /etc/systemd/system/

# Reload systemd
systemctl daemon-reload

# Enable services
echo_info "Enabling services..."
systemctl enable penny-api
systemctl enable penny-celery
systemctl enable penny-celery-beat

# Start services
echo_info "Starting services..."
systemctl start penny-api
systemctl start penny-celery
systemctl start penny-celery-beat

# Check service status
echo_info "Checking service status..."
echo ""
echo "=== Service Status ==="
systemctl status penny-api --no-pager -l || true
echo ""
systemctl status penny-celery --no-pager -l || true
echo ""
systemctl status penny-celery-beat --no-pager -l || true

echo ""
echo_info "Deployment complete!"
echo ""
echo "=== Next Steps ==="
echo "1. Create database: sudo -u postgres bash deploy/cloudpanel/setup-db.sh"
echo "2. Configure .env file in ${BACKEND_DIR}/.env"
echo "3. Run database migrations: cd ${BACKEND_DIR} && source venv/bin/activate && alembic upgrade head"
echo "4. Add Nginx vhost configuration in CloudPanel admin panel"
echo "5. Configure SSL certificate in CloudPanel"
echo ""
echo "=== Log Files ==="
echo "API logs:         ${LOG_DIR}/api.log"
echo "API errors:       ${LOG_DIR}/api-error.log"
echo "Celery logs:      ${LOG_DIR}/celery.log"
echo "Celery errors:    ${LOG_DIR}/celery-error.log"
echo "Celery beat logs: ${LOG_DIR}/celery-beat.log"
echo ""
echo "=== Service Commands ==="
echo "Restart API:    sudo systemctl restart penny-api"
echo "Restart Celery: sudo systemctl restart penny-celery penny-celery-beat"
echo "View logs:      sudo journalctl -u penny-api -f"
