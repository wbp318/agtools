# AgTools Production Deployment Guide

This guide covers deploying AgTools to a production environment.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Quick Start (Docker)](#quick-start-docker)
3. [Manual Deployment](#manual-deployment)
4. [Database Setup](#database-setup)
5. [Environment Configuration](#environment-configuration)
6. [Reverse Proxy (Nginx)](#reverse-proxy-nginx)
7. [SSL/HTTPS Setup](#sslhttps-setup)
8. [Monitoring](#monitoring)
9. [Backup & Recovery](#backup--recovery)
10. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Minimum Server Requirements

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| CPU | 2 cores | 4 cores |
| RAM | 2 GB | 4 GB |
| Storage | 20 GB | 50 GB SSD |
| OS | Ubuntu 22.04 LTS | Ubuntu 22.04 LTS |

### Required Software

- Docker & Docker Compose (recommended)
- OR Python 3.10+ and PostgreSQL 15+
- Nginx (for reverse proxy)
- Certbot (for SSL)

---

## Quick Start (Docker)

The fastest way to deploy AgTools is with Docker.

### 1. Clone the Repository

```bash
git clone https://github.com/wbp318/agtools.git
cd agtools
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit with your production values
nano .env
```

**Required environment variables:**

```bash
# SECURITY - Generate a strong secret key
SECRET_KEY=your-super-secret-key-min-32-chars

# Database (Docker will use these)
DATABASE_URL=postgresql://agtools:your-db-password@db:5432/agtools

# Email (for notifications)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
FROM_EMAIL=notifications@yourdomain.com
```

### 3. Start Services

```bash
# Start in detached mode
docker-compose up -d

# Check status
docker-compose ps

# View logs
docker-compose logs -f api
```

### 4. Initialize Database

```bash
# Run database migrations (first time only)
docker-compose exec api python -c "from database import init_db; init_db()"
```

### 5. Verify Deployment

```bash
# Health check
curl http://localhost:8000/

# API docs
open http://localhost:8000/docs
```

---

## Manual Deployment

For deployments without Docker.

### 1. Install System Dependencies

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Python
sudo apt install python3.11 python3.11-venv python3-pip -y

# Install PostgreSQL
sudo apt install postgresql postgresql-contrib -y
```

### 2. Create Application User

```bash
# Create system user
sudo useradd -m -s /bin/bash agtools
sudo su - agtools

# Clone repository
git clone https://github.com/wbp318/agtools.git
cd agtools
```

### 3. Set Up Virtual Environment

```bash
# Create and activate venv
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r backend/requirements.txt
```

### 4. Configure Environment

```bash
# Create .env file
cp .env.example .env
nano .env  # Edit with production values
```

### 5. Create Systemd Service

```bash
sudo nano /etc/systemd/system/agtools.service
```

```ini
[Unit]
Description=AgTools API Server
After=network.target postgresql.service

[Service]
Type=simple
User=agtools
Group=agtools
WorkingDirectory=/home/agtools/agtools/backend
Environment="PATH=/home/agtools/agtools/venv/bin"
EnvironmentFile=/home/agtools/agtools/.env
ExecStart=/home/agtools/agtools/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable agtools
sudo systemctl start agtools

# Check status
sudo systemctl status agtools
```

---

## Database Setup

### PostgreSQL Configuration

```bash
# Access PostgreSQL
sudo -u postgres psql

# Create database and user
CREATE USER agtools WITH PASSWORD 'your-secure-password';
CREATE DATABASE agtools OWNER agtools;
GRANT ALL PRIVILEGES ON DATABASE agtools TO agtools;
\q
```

### Run Migrations

```bash
# Apply schema
psql -U agtools -d agtools -f database/schema.sql

# Load seed data (optional)
cd backend
python -c "from database.seed_data import seed_all; seed_all()"
```

### PostgreSQL Tuning (Optional)

Edit `/etc/postgresql/15/main/postgresql.conf`:

```conf
# Memory
shared_buffers = 256MB
effective_cache_size = 768MB
work_mem = 16MB

# Connections
max_connections = 100

# Logging
log_statement = 'mod'
log_duration = on
```

---

## Environment Configuration

### Complete .env Reference

```bash
# ===================
# REQUIRED
# ===================

# Security key (min 32 characters, use: openssl rand -hex 32)
SECRET_KEY=your-super-secret-key-change-this

# Database connection
DATABASE_URL=postgresql://agtools:password@localhost:5432/agtools

# ===================
# EMAIL (Optional but recommended)
# ===================

SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-specific-password
FROM_EMAIL=agtools@yourdomain.com
FROM_NAME=AgTools Notifications

# ===================
# AI SERVICES (Optional)
# ===================

HUGGING_FACE_TOKEN=your-hf-token
WEATHER_API_KEY=your-weather-api-key

# ===================
# DEVELOPMENT
# ===================

DEBUG=false
LOG_LEVEL=info
```

### Generating a Secret Key

```bash
# Option 1: OpenSSL
openssl rand -hex 32

# Option 2: Python
python -c "import secrets; print(secrets.token_hex(32))"
```

---

## Reverse Proxy (Nginx)

### Install Nginx

```bash
sudo apt install nginx -y
```

### Configure Site

```bash
sudo nano /etc/nginx/sites-available/agtools
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 86400;
    }

    # Static files (if serving from Nginx)
    location /static/ {
        alias /home/agtools/agtools/backend/static/;
        expires 30d;
    }

    # Health check endpoint
    location /health {
        proxy_pass http://127.0.0.1:8000/;
        access_log off;
    }
}
```

```bash
# Enable site
sudo ln -s /etc/nginx/sites-available/agtools /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## SSL/HTTPS Setup

### Using Certbot (Let's Encrypt)

```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx -y

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal (already configured, but verify)
sudo certbot renew --dry-run
```

### Manual Certificate

If using a purchased certificate:

```bash
sudo nano /etc/nginx/sites-available/agtools
```

```nginx
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/your-cert.pem;
    ssl_certificate_key /etc/ssl/private/your-key.pem;

    # Modern SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256;
    ssl_prefer_server_ciphers off;

    # ... rest of config
}

# Redirect HTTP to HTTPS
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}
```

---

## Monitoring

### Basic Health Checks

```bash
# Create monitoring script
nano /home/agtools/health_check.sh
```

```bash
#!/bin/bash
HEALTH_URL="http://localhost:8000/"
ALERT_EMAIL="admin@yourdomain.com"

response=$(curl -s -o /dev/null -w "%{http_code}" $HEALTH_URL)

if [ "$response" != "200" ]; then
    echo "AgTools is DOWN! HTTP $response" | mail -s "AgTools Alert" $ALERT_EMAIL
    # Attempt restart
    sudo systemctl restart agtools
fi
```

```bash
# Add to crontab (check every 5 minutes)
crontab -e
*/5 * * * * /home/agtools/health_check.sh
```

### Log Monitoring

```bash
# View application logs
# Docker
docker-compose logs -f api

# Systemd
journalctl -u agtools -f

# Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

### Recommended Monitoring Tools

- **Uptime**: UptimeRobot, Pingdom (free tiers available)
- **Metrics**: Prometheus + Grafana
- **Logs**: Loki, ELK Stack
- **APM**: Sentry (error tracking)

---

## Backup & Recovery

### Database Backup

```bash
# Create backup script
nano /home/agtools/backup.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/home/agtools/backups"
DATE=$(date +%Y%m%d_%H%M%S)
RETENTION_DAYS=30

mkdir -p $BACKUP_DIR

# Docker
docker-compose exec -T db pg_dump -U agtools agtools > $BACKUP_DIR/agtools_$DATE.sql

# OR Manual
# pg_dump -U agtools agtools > $BACKUP_DIR/agtools_$DATE.sql

# Compress
gzip $BACKUP_DIR/agtools_$DATE.sql

# Delete old backups
find $BACKUP_DIR -name "*.sql.gz" -mtime +$RETENTION_DAYS -delete

echo "Backup completed: agtools_$DATE.sql.gz"
```

```bash
chmod +x /home/agtools/backup.sh

# Schedule daily backup at 2 AM
crontab -e
0 2 * * * /home/agtools/backup.sh >> /home/agtools/backup.log 2>&1
```

### Restore from Backup

```bash
# Docker
gunzip -c backups/agtools_20250101_020000.sql.gz | docker-compose exec -T db psql -U agtools agtools

# Manual
gunzip -c backups/agtools_20250101_020000.sql.gz | psql -U agtools agtools
```

### Application Backup

```bash
# Backup uploads and data
tar -czvf agtools_files_$(date +%Y%m%d).tar.gz data/ uploads/
```

---

## Troubleshooting

### Common Issues

#### API Won't Start

```bash
# Check logs
docker-compose logs api
# OR
journalctl -u agtools -n 100

# Common causes:
# - Database not running
# - Invalid environment variables
# - Port already in use
```

#### Database Connection Failed

```bash
# Test connection
psql -U agtools -h localhost -d agtools

# Check PostgreSQL status
sudo systemctl status postgresql

# Verify credentials in .env
```

#### 502 Bad Gateway (Nginx)

```bash
# Check if API is running
curl http://localhost:8000/

# Check Nginx config
sudo nginx -t

# Check Nginx logs
tail -f /var/log/nginx/error.log
```

#### High Memory Usage

```bash
# Check memory
free -h

# Restart services
docker-compose restart
# OR
sudo systemctl restart agtools
```

### Getting Help

- **GitHub Issues**: https://github.com/wbp318/agtools/issues
- **API Docs**: https://your-domain.com/docs
- **Logs**: Always include relevant log output when reporting issues

---

## Security Checklist

Before going live:

- [ ] Strong SECRET_KEY generated and set
- [ ] Database password changed from default
- [ ] SSL/HTTPS enabled
- [ ] Firewall configured (only 80, 443, 22 open)
- [ ] .env file permissions restricted (chmod 600)
- [ ] Debug mode disabled
- [ ] Regular backups scheduled
- [ ] Monitoring alerts configured

```bash
# Firewall setup
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable

# Restrict .env permissions
chmod 600 .env
```

---

## Updating AgTools

```bash
# Docker deployment
cd /home/agtools/agtools
git pull origin master
docker-compose down
docker-compose build
docker-compose up -d

# Manual deployment
cd /home/agtools/agtools
git pull origin master
source venv/bin/activate
pip install -r backend/requirements.txt
sudo systemctl restart agtools
```

---

*Last updated: December 2025*
