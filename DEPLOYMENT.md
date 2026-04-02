# Production Deployment Guide

## Free Hosting Options

### Option 1: InfinityFree (100% Free Forever)
- **URL**: https://infinityfree.net
- **Features**:
  - Unlimited bandwidth & disk space
  - MySQL databases
  - PHP 7.4+
  - Free subdomain or custom domain
  - cPanel control panel
  - WordPress/WooCommerce installer

### Option 2: 000webhost (Free Tier)
- **URL**: https://www.000webhost.com
- **Features**:
  - 300 MB disk space
  - 3 GB bandwidth
  - 1 website
  - MySQL database
  - WordPress installer

### Option 3: AWS Free Tier (12 Months Free)
- **URL**: https://aws.amazon.com/free
- **Features**:
  - EC2 t2.micro instance
  - 750 hours/month
  - 30 GB storage
  - 15 GB bandwidth

## WordPress + WooCommerce Setup

### Step 1: Install WordPress

#### On InfinityFree/000webhost:
1. Login to cPanel
2. Find "Softaculous Apps Installer"
3. Select "WordPress"
4. Click "Install Now"
5. Fill in:
   - Site Name: Your Brand Name
   - Admin Email
   - Admin Username
   - Admin Password
6. Click "Install"

#### On AWS/VPS:
```bash
# Install LAMP stack
sudo apt update
sudo apt install apache2 mysql-server php libapache2-mod-php php-mysql

# Download WordPress
cd /var/www/html
sudo wget https://wordpress.org/latest.tar.gz
sudo tar -xzf latest.tar.gz
sudo mv wordpress/* .
sudo chown -R www-data:www-data /var/www/html

# Configure database
sudo mysql -u root -p
CREATE DATABASE wordpress;
CREATE USER 'wpuser'@'localhost' IDENTIFIED BY 'password';
GRANT ALL PRIVILEGES ON wordpress.* TO 'wpuser'@'localhost';
FLUSH PRIVILEGES;
EXIT;

# Complete WordPress installation via web browser
# Visit: http://your-domain.com/wp-admin/install.php
```

### Step 2: Install WooCommerce

1. Login to WordPress Admin
2. Go to Plugins → Add New
3. Search "WooCommerce"
4. Click "Install Now" → "Activate"
5. Follow WooCommerce Setup Wizard:
   - Store Details (Address, Currency)
   - Industry (Your Niche)
   - Product Types (Physical products)
   - Business Details
   - Skip Theme (we'll configure programmatically)

### Step 3: Generate WooCommerce API Keys

1. Go to WooCommerce → Settings → Advanced → REST API
2. Click "Add Key"
3. Fill in:
   - Description: "Auto Store Automation"
   - User: Select admin user
   - Permissions: Read/Write
4. Click "Generate API Key"
5. **Save these keys** - you'll need them for `.env`:
   - Consumer Key
   - Consumer Secret

## Python Backend Setup

### On VPS (Ubuntu)

```bash
# Install Python and dependencies
sudo apt update
sudo apt install python3 python3-pip python3-venv

# Create project directory
sudo mkdir /opt/auto-store
cd /opt/auto-store

# Upload project files (via SFTP or git)
# Or clone from repository:
# git clone <your-repo-url> .

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create .env file
cp .env.example .env
nano .env  # Edit with your credentials
```

### Configure .env

```bash
# WordPress/WooCommerce
WP_API_URL=https://yourdomain.com
WP_USER=your_wp_username
WP_APP_PASSWORD=your_woocommerce_consumer_key

# Stripe (Free Test Account)
STRIPE_SECRET_KEY=sk_test_your_key
STRIPE_PUBLISHABLE_KEY=pk_test_your_key

# PayPal Sandbox (Free)
PAYPAL_CLIENT_ID=your_client_id
PAYPAL_SECRET=your_secret

# Gmail SMTP (Free)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=yourEmail@gmail.com
SMTP_PASSWORD=your_app_password

# Google Analytics (Free)
GA_MEASUREMENT_ID=G-XXXXXXXXXX

# Meta Pixel (Free)
META_PIXEL_ID=123456789

# Database
DB_PATH=/opt/auto-store/store_automation.db

# Webhook
WEBHOOK_SECRET=generate_random_secret_here
WEBHOOK_PORT=8080
```

## Setup Systemd Services

### 1. Webhook Service

```bash
sudo nano /etc/systemd/system/auto-store-webhook.service
```

```ini
[Unit]
Description=Auto Store Webhook Server
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/auto-store
Environment="PATH=/opt/auto-store/venv/bin"
ExecStart=/opt/auto-store/venv/bin/python /opt/auto-store/webhooks.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable auto-store-webhook
sudo systemctl start auto-store-webhook
```

### 2. Cron Scheduler Service

```bash
sudo nano /etc/systemd/system/auto-store-cron.service
```

```ini
[Unit]
Description=Auto Store Cron Scheduler
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/auto-store
Environment="PATH=/opt/auto-store/venv/bin"
ExecStart=/opt/auto-store/venv/bin/python /opt/auto-store/cron_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable auto-store-cron
sudo systemctl start auto-store-cron
```

## Nginx Configuration

### Install Nginx

```bash
sudo apt install nginx
```

### Configure Reverse Proxy for Webhooks

```bash
sudo nano /etc/nginx/sites-available/auto-store
```

```nginx
server {
    listen 80;
    server_name webhooks.yourdomain.com;

    location / {
        proxy_pass http://localhost:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
sudo ln -s /etc/nginx/sites-available/auto-store /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate (Free with Let's Encrypt)

```bash
sudo apt install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
sudo certbot --nginx -d webhooks.yourdomain.com
```

## Firewall Configuration

```bash
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

## Payment Gateway Setup

### Stripe

1. Create free account: https://stripe.com
2. Go to Developers → API Keys
3. Copy keys to `.env`
4. Setup webhook:
   - Go to Developers → Webhooks
   - Add endpoint: `https://webhooks.yourdomain.com/webhooks/stripe`
   - Select events:
     - `payment_intent.succeeded`
     - `payment_intent.payment_failed`
     - `charge.refunded`
5. Copy webhook secret to `.env`

### PayPal

1. Create sandbox account: https://developer.paypal.com
2. Create app in Dashboard
3. Copy Client ID and Secret to `.env`
4. Setup webhook:
   - Dashboard → My Apps → Select App → Webhooks
   - Add webhook: `https://webhooks.yourdomain.com/webhooks/paypal`
   - Select events:
     - `PAYMENT.CAPTURE.COMPLETED`
     - `PAYMENT.CAPTURE.DENIED`

## WooCommerce Webhook Setup

1. Login to WordPress Admin
2. Go to WooCommerce → Settings → Advanced → Webhooks
3. Add webhook for each event:

#### New Order Webhook
- Status: Active
- Topic: Order created
- Delivery URL: `https://webhooks.yourdomain.com/webhooks/woocommerce`
- Secret: (copy from `.env` WEBHOOK_SECRET)

#### Order Updated Webhook
- Status: Active
- Topic: Order updated
- Delivery URL: `https://webhooks.yourdomain.com/webhooks/woocommerce`
- Secret: (same as above)

## Testing

### Test Webhook Server

```bash
curl http://localhost:8080/health
# Should return: {"status":"healthy"}
```

### Test Store Creation

```bash
cd /opt/auto-store
source venv/bin/activate
python main.py --example
```

### Monitor Services

```bash
# Check webhook service
sudo systemctl status auto-store-webhook

# Check cron service
sudo systemctl status auto-store-cron

# View logs
sudo journalctl -u auto-store-webhook -f
sudo journalctl -u auto-store-cron -f
```

## Monitoring & Maintenance

### Check Database Logs

```bash
sqlite3 /opt/auto-store/store_automation.db
SELECT * FROM automation_logs ORDER BY created_at DESC LIMIT 10;
```

### Check Webhook Queue

```bash
sqlite3 /opt/auto-store/store_automation.db
SELECT * FROM webhooks WHERE processed = 0;
```

### Backup Database

```bash
# Add to crontab for daily backups
0 3 * * * cp /opt/auto-store/store_automation.db /opt/auto-store/backups/db_$(date +\%Y\%m\%d).db
```

## Troubleshooting

### Webhooks Not Receiving

1. Check firewall: `sudo ufw status`
2. Check Nginx: `sudo nginx -t`
3. Check service: `sudo systemctl status auto-store-webhook`
4. Check logs: `sudo journalctl -u auto-store-webhook -n 50`

### Jobs Not Running

1. Check cron service: `sudo systemctl status auto-store-cron`
2. Check logs: `sudo journalctl -u auto-store-cron -n 50`
3. Verify database path in `.env`

### Payment Processing Failing

1. Verify API keys in `.env`
2. Check payment gateway logs in database
3. Test with small amount ($0.50)
4. Verify webhook URLs are accessible

## Production Checklist

- [ ] WordPress + WooCommerce installed
- [ ] WooCommerce API keys generated
- [ ] Python backend deployed
- [ ] `.env` configured with all credentials
- [ ] Systemd services running
- [ ] Nginx reverse proxy configured
- [ ] SSL certificates installed
- [ ] Firewall configured
- [ ] Payment webhooks configured
- [ ] WooCommerce webhooks configured
- [ ] Test store creation successful
- [ ] Test order processing
- [ ] Email notifications working
- [ ] Analytics tracking installed
- [ ] Backup system configured
- [ ] Monitoring setup

## Scaling

### Multiple Stores

The system supports multiple stores. Each store gets:
- Unique store_id in database
- Separate automation context
- Independent webhook processing
- Isolated job execution

### Load Balancing

For high traffic:
1. Deploy multiple webhook instances
2. Use Nginx upstream load balancing
3. Consider Redis for job queue
4. Upgrade to PostgreSQL from SQLite

## Cost Breakdown (Monthly)

| Service | Cost |
|---------|------|
| InfinityFree Hosting | $0 |
| Stripe (no monthly fee) | 2.9% + $0.30 per transaction |
| PayPal | 2.9% + $0.30 per transaction |
| Gmail SMTP | $0 |
| Google Analytics | $0 |
| Meta Pixel | $0 |
| TinyPNG (500/month) | $0 |
| **Total Fixed Costs** | **$0** |

Only pay transaction fees when you make sales!
