# Penny Stock Picker - CloudPanel Deployment Guide

This guide walks you through deploying the Penny Stock Picker application on a CloudPanel server.

## Prerequisites

- Ubuntu 22.04 LTS server with CloudPanel installed
- Domain pointed to your server (penny.co-l.in)
- SSH access with root privileges
- Python 3.12
- Minimum 4GB RAM (8GB recommended)
- 50GB+ SSD storage

## Step 1: Create Site in CloudPanel

1. Log into CloudPanel admin panel
2. Go to **Sites** → **Add Site**
3. Select **"Create a Python Site"**
4. Configure:
   - Domain: `penny.co-l.in`
   - Python Version: **3.12**
   - Site User: `penny` (default)
5. Click **Create**

## Step 2: Clone Repository

SSH into your server and clone the repository:

```bash
cd /home/penny/htdocs/penny.co-l.in
git clone https://github.com/colin-cd72/penny.git .
```

## Step 3: Run Deployment Script

```bash
sudo bash deploy/cloudpanel/deploy.sh
```

This script will:
- Install Python 3.11, Node.js 20, Redis
- Install TimescaleDB extension for PostgreSQL
- Create Python virtual environment and install dependencies
- Build the React frontend
- Install and enable systemd services

## Step 4: Setup Database

Run the database setup script:

```bash
sudo -u postgres bash deploy/cloudpanel/setup-db.sh
```

**Save the credentials** shown at the end - you'll need them for the `.env` file.

## Step 5: Configure Environment Variables

Create the `.env` file in the backend directory:

```bash
cd /home/penny/htdocs/penny.co-l.in/backend
cp .env.example .env
nano .env
```

Update these required values:

```env
# Database (from Step 4)
DATABASE_URL=postgresql+asyncpg://penny:YOUR_PASSWORD@localhost:5432/penny_stock

# Security - generate a secure key
SECRET_KEY=your-secret-key-generate-with-openssl-rand-hex-32

# API Keys (sign up for each service)
POLYGON_API_KEY=your-polygon-api-key
SEC_API_KEY=your-sec-api-key
BENZINGA_API_KEY=your-benzinga-api-key

# Alpaca Broker (for trading)
ALPACA_API_KEY=your-alpaca-key
ALPACA_API_SECRET=your-alpaca-secret
ALPACA_BASE_URL=https://paper-api.alpaca.markets  # Use paper trading first!

# Notifications
SENDGRID_API_KEY=your-sendgrid-key
TWILIO_ACCOUNT_SID=your-twilio-sid
TWILIO_AUTH_TOKEN=your-twilio-token
TWILIO_PHONE_NUMBER=+1234567890

# Application
FRONTEND_URL=https://penny.co-l.in
CORS_ORIGINS=["https://penny.co-l.in"]
```

Set proper permissions:

```bash
chown penny:penny .env
chmod 600 .env
```

## Step 6: Run Database Migrations

```bash
cd /home/penny/htdocs/penny.co-l.in/backend
source venv/bin/activate
alembic upgrade head
deactivate
```

## Step 7: Configure Nginx in CloudPanel

1. Go to CloudPanel → **Sites** → **penny.co-l.in** → **Vhost**
2. Find the `server` block and add the configuration from `nginx-vhost.conf`:

```nginx
# Serve React frontend (static files)
location / {
    root /home/penny/htdocs/penny.co-l.in/frontend/dist;
    try_files $uri $uri/ /index.html;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}

# Proxy API requests to FastAPI backend
location /api {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # Timeouts
    proxy_connect_timeout 60s;
    proxy_send_timeout 60s;
    proxy_read_timeout 60s;
}

# WebSocket support for real-time updates
location /api/v1/ws {
    proxy_pass http://127.0.0.1:8000;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
    proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    proxy_set_header X-Forwarded-Proto $scheme;

    # WebSocket timeouts
    proxy_connect_timeout 7d;
    proxy_send_timeout 7d;
    proxy_read_timeout 7d;
}

# Health check endpoint
location /health {
    proxy_pass http://127.0.0.1:8000/health;
    proxy_http_version 1.1;
    proxy_set_header Host $host;
}
```

3. Click **Save**
4. Test Nginx configuration: `sudo nginx -t`
5. Reload Nginx: `sudo systemctl reload nginx`

## Step 8: Enable SSL

1. Go to CloudPanel → **Sites** → **penny.co-l.in** → **SSL/TLS**
2. Click **Actions** → **New Let's Encrypt Certificate**
3. Wait for certificate to be issued

## Step 9: Start Services

```bash
sudo systemctl restart penny-api penny-celery penny-celery-beat
```

## Step 10: Verify Deployment

1. Check service status:
   ```bash
   sudo systemctl status penny-api
   sudo systemctl status penny-celery
   sudo systemctl status penny-celery-beat
   ```

2. Test API health endpoint:
   ```bash
   curl https://penny.co-l.in/health
   ```

3. Visit https://penny.co-l.in in your browser

---

## Managing Services

### View Logs

```bash
# API logs
tail -f /var/log/penny/api.log
tail -f /var/log/penny/api-error.log

# Celery worker logs
tail -f /var/log/penny/celery.log
tail -f /var/log/penny/celery-error.log

# Celery beat logs
tail -f /var/log/penny/celery-beat.log

# Systemd journal
sudo journalctl -u penny-api -f
sudo journalctl -u penny-celery -f
```

### Restart Services

```bash
# Restart all services
sudo systemctl restart penny-api penny-celery penny-celery-beat

# Restart individual service
sudo systemctl restart penny-api
```

### Stop/Start Services

```bash
sudo systemctl stop penny-api penny-celery penny-celery-beat
sudo systemctl start penny-api penny-celery penny-celery-beat
```

---

## Updating the Application

```bash
cd /home/penny/htdocs/penny.co-l.in

# Pull latest code
git pull origin main

# Update backend dependencies
cd backend
source venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
deactivate

# Rebuild frontend
cd ../frontend
npm install
npm run build

# Restart services
sudo systemctl restart penny-api penny-celery penny-celery-beat
```

---

## Troubleshooting

### API not responding

1. Check if service is running: `sudo systemctl status penny-api`
2. Check logs: `tail -50 /var/log/penny/api-error.log`
3. Verify port 8000 is listening: `netstat -tlnp | grep 8000`

### Database connection errors

1. Verify PostgreSQL is running: `sudo systemctl status postgresql`
2. Test connection: `psql -U penny -d penny_stock -h localhost`
3. Check DATABASE_URL in `.env` file

### Redis connection errors

1. Verify Redis is running: `sudo systemctl status redis-server`
2. Test connection: `redis-cli ping`

### Celery not processing tasks

1. Check Celery worker status: `sudo systemctl status penny-celery`
2. Check logs: `tail -50 /var/log/penny/celery-error.log`
3. Verify Redis is accessible

### Frontend not loading

1. Verify build exists: `ls -la frontend/dist/`
2. Check Nginx configuration: `sudo nginx -t`
3. Verify root path in Nginx config points to `frontend/dist`

---

## Security Recommendations

1. **Firewall**: Only expose ports 80 and 443
   ```bash
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

2. **Fail2ban**: Install to prevent brute force attacks
   ```bash
   sudo apt install fail2ban
   ```

3. **Regular updates**: Keep system packages updated
   ```bash
   sudo apt update && sudo apt upgrade
   ```

4. **Backup database**: Set up regular PostgreSQL backups
   ```bash
   pg_dump -U penny penny_stock > backup_$(date +%Y%m%d).sql
   ```

---

## API Keys Setup

### Polygon.io (Real-time prices)
1. Sign up at https://polygon.io
2. Choose Stocks Starter ($79/mo) or higher
3. Copy API key to `.env`

### SEC API (SEC filings)
1. Sign up at https://sec-api.io
2. Choose appropriate plan ($150-500/mo)
3. Copy API key to `.env`

### Benzinga (News)
1. Sign up at https://www.benzinga.com/apis
2. Choose News API plan
3. Copy API key to `.env`

### Alpaca (Trading)
1. Sign up at https://alpaca.markets
2. Start with paper trading account
3. Copy API key and secret to `.env`

### SendGrid (Email)
1. Sign up at https://sendgrid.com
2. Create API key with mail send permissions
3. Verify sender email address

### Twilio (SMS)
1. Sign up at https://twilio.com
2. Get phone number for SMS
3. Copy account SID and auth token
