#!/bin/bash
# Auto-deployment script triggered by GitHub webhook

set -e

APP_DIR="/home/penny/htdocs/penny.co-l.in"
LOG_FILE="/var/log/penny/webhook-deploy.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

log "=== Starting auto-deployment ==="

cd "$APP_DIR"

# Pull latest code
log "Pulling latest code..."
git fetch origin main
git reset --hard origin/main

# Update backend dependencies
log "Updating backend dependencies..."
cd "$APP_DIR/backend"
source venv/bin/activate
pip install -q -r requirements.txt

# Run migrations
log "Running database migrations..."
alembic upgrade head
deactivate

# Rebuild frontend
log "Building frontend..."
cd "$APP_DIR/frontend"
npm install --silent
npm run build

# Fix ownership
chown -R penny:penny "$APP_DIR"

# Restart services
log "Restarting services..."
systemctl restart penny-api penny-celery penny-celery-beat

log "=== Deployment complete ==="
