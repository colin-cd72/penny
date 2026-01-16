#!/bin/bash
# Penny Stock Picker - Database Setup Script
# Run this script as postgres user: sudo -u postgres bash setup-db.sh

set -e

# Configuration - customize these values
DB_NAME="penny_stock"
DB_USER="penny"
DB_PASSWORD="${DB_PASSWORD:-$(openssl rand -base64 32)}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
echo_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
echo_error() { echo -e "${RED}[ERROR]${NC} $1"; }

echo_info "Setting up PostgreSQL database for Penny Stock Picker..."

# Check if running as postgres user
if [ "$(whoami)" != "postgres" ]; then
    echo_error "This script must be run as the postgres user"
    echo_info "Run: sudo -u postgres bash setup-db.sh"
    exit 1
fi

# Check if database already exists
if psql -lqt | cut -d \| -f 1 | grep -qw ${DB_NAME}; then
    echo_warn "Database '${DB_NAME}' already exists"
    read -p "Do you want to drop and recreate it? (y/N): " confirm
    if [ "$confirm" = "y" ] || [ "$confirm" = "Y" ]; then
        echo_info "Dropping existing database..."
        psql -c "DROP DATABASE IF EXISTS ${DB_NAME};"
        psql -c "DROP USER IF EXISTS ${DB_USER};"
    else
        echo_info "Keeping existing database. Exiting."
        exit 0
    fi
fi

# Create user
echo_info "Creating database user '${DB_USER}'..."
psql -c "CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';"

# Create database
echo_info "Creating database '${DB_NAME}'..."
psql -c "CREATE DATABASE ${DB_NAME} OWNER ${DB_USER};"

# Grant privileges
echo_info "Granting privileges..."
psql -c "GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};"

# Connect to database and setup extensions
echo_info "Setting up database extensions..."
psql -d ${DB_NAME} << EOF
-- Enable TimescaleDB for time-series data
CREATE EXTENSION IF NOT EXISTS timescaledb;

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Enable full-text search
CREATE EXTENSION IF NOT EXISTS pg_trgm;

-- Grant schema privileges
GRANT ALL ON SCHEMA public TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${DB_USER};
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${DB_USER};
EOF

echo ""
echo_info "Database setup complete!"
echo ""
echo "=== Database Credentials ==="
echo "Host:     localhost"
echo "Port:     5432"
echo "Database: ${DB_NAME}"
echo "Username: ${DB_USER}"
echo "Password: ${DB_PASSWORD}"
echo ""
echo "=== Connection String ==="
echo "postgresql://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"
echo ""
echo "=== Add to .env file ==="
echo "DATABASE_URL=postgresql+asyncpg://${DB_USER}:${DB_PASSWORD}@localhost:5432/${DB_NAME}"
echo ""
echo_warn "IMPORTANT: Save these credentials securely!"
echo_warn "The password was auto-generated and will not be shown again."
