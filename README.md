# Auto Online Store Setup System

Complete automation system for creating and managing ecommerce stores using **100% free tools**.

## Features

✅ **Automated Store Creation** - WooCommerce-based stores (free alternative to Shopify)  
✅ **Brand Asset Generation** - Auto-generate logos, color palettes, taglines  
✅ **Product Import** - Dropshipping integration with CJ, AliExpress  
✅ **Payment Processing** - Stripe, PayPal, Razorpay integration  
✅ **Email Automation** - Order confirmations, cart recovery, notifications  
✅ **Analytics Tracking** - Google Analytics & Meta Pixel integration  
✅ **Webhook Processing** - Real-time event handling  
✅ **Scheduled Jobs** - Daily/weekly/monthly maintenance automation  

## Architecture

```
┌─────────────────────────────────────────────────────┐
│               User Input Collection                  │
│  (Niche, Country, Brand, Payment, Products)         │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│            Brand Asset Generation                    │
│  (Logo, Colors, Tagline, Brand Voice)               │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│          WooCommerce Store Setup                     │
│  (Pages, Theme, Settings, Currency)                 │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│            Product Import & Processing               │
│  (Title Rewrite, Pricing, Images, Variants)         │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│           Payment Gateway Setup                      │
│  (Stripe/PayPal/Razorpay + Test Transaction)        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│          Automation Rules Configuration              │
│  (Order Processing, Cart Recovery, Emails)          │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│        Analytics & Tracking Integration              │
│  (Google Analytics, Meta Pixel, Conversions)        │
└──────────────────┬──────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────────────┐
│              Store Activation                        │
│  (Live & Ready for Sales)                           │
└─────────────────────────────────────────────────────┘
```

## Free Tools Used

| Component | Free Tool | Sign Up URL |
|-----------|-----------|-------------|
| Ecommerce Platform | **WooCommerce** (WordPress) | https://wordpress.org |
| Payment Gateway | **Stripe** (free account) | https://stripe.com |
| Payment Gateway | **PayPal** (sandbox) | https://developer.paypal.com |
| Email Service | **Gmail SMTP** | Use your Gmail |
| Analytics | **Google Analytics** | https://analytics.google.com |
| Analytics | **Meta Pixel** | https://business.facebook.com |
| Image Compression | **TinyPNG** (500/month free) | https://tinypng.com/developers |
| Hosting | **InfinityFree** or **000webhost** | https://infinityfree.net |

## Installation

### 1. Prerequisites

- Python 3.8+
- WordPress installation with WooCommerce plugin
- Free accounts for payment gateways

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your credentials
```

### 4. Initialize Database

```bash
python -c "from database import Database; from config import CONFIG; db = Database(CONFIG.DB_PATH)"
```

## Usage

### Quick Start (Example Data)

```bash
python main.py --example
```

### Programmatic Usage

```python
from main import StoreOrchestrator

# Define store configuration
store_config = {
    'niche': 'fitness',
    'country': 'US',
    'brand_name': 'FitPro',
    'auto_logo': True,
    'payment_gateway': 'stripe',
    'product_source': 'cj',
    'color_scheme': 'modern'
}

# Create store
orchestrator = StoreOrchestrator()
result = orchestrator.create_store_automated(store_config)

print(f"Store ID: {result['store_id']}")
print(f"Success: {result['success']}")
```

### Start Webhook Server

```bash
python webhooks.py
```

The webhook server will listen on port 8080 (configurable) for:
- Stripe webhooks: `/webhooks/stripe`
- PayPal webhooks: `/webhooks/paypal`
- WooCommerce webhooks: `/webhooks/woocommerce`

### Start Cron Scheduler

```bash
# Run continuously
python cron_scheduler.py

# Or run specific jobs
python cron_scheduler.py daily
python cron_scheduler.py weekly
python cron_scheduler.py monthly
```

### Setup Cron Jobs (Production)

#### Option 1: Systemd Service

```bash
python cron_scheduler.py setup-systemd
sudo cp auto-store-cron.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable auto-store-cron
sudo systemctl start auto-store-cron
```

#### Option 2: Traditional Crontab

```bash
python cron_scheduler.py setup-crontab
crontab crontab.txt
```

## Configuration

### Supported Countries

| Country Code | Currency | Payment Gateways |
|-------------|----------|------------------|
| US | USD | Stripe, PayPal |
| CA | CAD | Stripe, PayPal |
| GB | GBP | Stripe, PayPal |
| AU | AUD | Stripe, PayPal |
| IN | INR | Razorpay, PayPal |
| SG | SGD | Stripe, PayPal |
| AE | AED | Stripe, PayPal |

### Product Sources

- **CJ Dropshipping** - Requires API key
- **AliExpress** - Requires API key
- **Manual** - Manual product entry

### Automation Jobs

#### Daily (2 AM)
- Sync inventory with suppliers
- Check payment statuses
- Remove out-of-stock products

#### Weekly (Sunday 3 AM)
- Update trending products
- Adjust pricing margins

#### Monthly (1st, 4 AM)
- Backup store data
- Generate performance reports

## API Integration

### WooCommerce Setup

1. Install WordPress + WooCommerce
2. Generate REST API keys:
   - WooCommerce → Settings → Advanced → REST API
   - Click "Add Key"
   - Set permissions to Read/Write
3. Add credentials to `.env`

### Payment Gateway Setup

#### Stripe

1. Sign up at https://stripe.com
2. Get API keys from Dashboard → Developers → API Keys
3. Add to `.env`:
   ```
   STRIPE_SECRET_KEY=sk_test_...
   STRIPE_PUBLISHABLE_KEY=pk_test_...
   ```

#### PayPal

1. Sign up at https://developer.paypal.com
2. Create app in Dashboard
3. Get Client ID and Secret
4. Add to `.env`

### Analytics Setup

#### Google Analytics

1. Create property at https://analytics.google.com
2. Copy Measurement ID (G-XXXXXXXXXX)
3. Add to `.env`

#### Meta Pixel

1. Create pixel at https://business.facebook.com
2. Copy Pixel ID
3. Add to `.env`

## File Structure

```
.
├── config.py                 # Configuration & constants
├── database.py              # SQLite database models
├── user_inputs.py           # Input collection & validation
├── brand_generator.py       # Brand asset generation
├── store_setup.py           # WooCommerce store setup
├── product_importer.py      # Product import & processing
├── payment_gateways.py      # Payment integration
├── automation_engine.py     # Email & event automation
├── analytics.py             # Analytics integration
├── webhooks.py              # Webhook server & processing
├── cron_scheduler.py        # Scheduled job management
├── main.py                  # Main orchestrator
├── requirements.txt         # Python dependencies
├── .env.example            # Environment template
└── README.md               # Documentation
```

## Database Schema

### Stores
- Store configuration and status

### Brand Assets
- Logos, colors, taglines

### Products
- Product catalog with pricing

### Orders
- Order tracking and fulfillment

### Abandoned Carts
- Cart recovery system

### Automation Logs
- Job execution history

### Payment Configs
- Gateway configurations

### Webhooks
- Event queue and retry logic

## Security

- All API keys in environment variables
- Webhook signature verification
- SQL injection protection (parameterized queries)
- Rate limiting on webhook processing
- Retry logic with exponential backoff

## Error Handling

- Comprehensive try-catch blocks
- Database logging of all errors
- Retry logic for API failures
- Webhook retry queue (max 3 attempts)

## Production Deployment

### Recommended Stack

- **Hosting**: VPS (DigitalOcean, Linode, Vultr)
- **OS**: Ubuntu 22.04 LTS
- **Web Server**: Nginx
- **Process Manager**: Systemd
- **Database**: SQLite (or upgrade to PostgreSQL)

### Deployment Steps

1. Clone repository to server
2. Install dependencies
3. Configure `.env`
4. Setup systemd services
5. Configure Nginx reverse proxy
6. Setup SSL with Let's Encrypt
7. Configure firewall

## Monitoring

- Check automation logs in database
- Monitor webhook processing queue
- Review daily/weekly/monthly job logs
- Track store performance metrics

## Support

For issues or questions:
- Review automation logs in database
- Check webhook retry queue
- Verify API credentials in `.env`
- Ensure WooCommerce API access

## License

MIT License - Free for commercial and personal use

## Contributing

Contributions welcome! Areas for improvement:
- Additional payment gateways
- More product suppliers
- Advanced analytics
- Multi-store management
- UI dashboard
