# API Documentation

## Store Creation API

### Create Store

```python
from main import StoreOrchestrator

orchestrator = StoreOrchestrator()
result = orchestrator.create_store_automated({
    'niche': 'fitness',
    'country': 'US',
    'brand_name': 'FitPro',
    'auto_logo': True,
    'payment_gateway': 'stripe',
    'product_source': 'cj',
    'color_scheme': 'modern'
})
```

**Parameters:**

| Parameter | Type | Required | Options | Description |
|-----------|------|----------|---------|-------------|
| `niche` | string | Yes | Any | Store category/niche |
| `country` | string | Yes | US, CA, GB, AU, IN, SG, AE, EU | Target country |
| `brand_name` | string | Yes | 2-50 chars | Brand name |
| `auto_logo` | boolean | No | true, false | Auto-generate logo |
| `payment_gateway` | string | Yes | stripe, paypal, razorpay | Payment provider |
| `product_source` | string | Yes | cj, aliexpress, manual | Product supplier |
| `color_scheme` | string | No | modern, minimal, vibrant, nature, tech, luxury | Color palette |

**Response:**

```json
{
  "store_id": 1,
  "success": true,
  "steps_completed": [
    "inputs_collected",
    "brand_assets_generated",
    "store_created",
    "store_configured",
    "products_imported",
    "payment_configured",
    "automation_configured",
    "analytics_configured",
    "store_finalized"
  ],
  "errors": [],
  "execution_time": 45.23
}
```

## Database API

### Create Store Record

```python
from database import Database
from config import CONFIG

db = Database(CONFIG.DB_PATH)

store_id = db.create_store({
    'store_name': 'FitPro',
    'niche': 'fitness',
    'country': 'US',
    'brand_name': 'FitPro',
    'currency': 'USD',
    'timezone': 'America/New_York'
})
```

### Save Brand Assets

```python
db.save_brand_assets(store_id, {
    'logo_url': '/path/to/logo.svg',
    'color_palette': ['#2C3E50', '#E74C3C', '#ECF0F1'],
    'tagline': 'Your Fitness Partner',
    'brand_voice': 'Motivational and energetic'
})
```

### Create Product

```python
product_id = db.create_product(store_id, {
    'supplier_id': 'CJ-12345',
    'title': 'Premium Yoga Mat',
    'description': 'High-quality yoga mat...',
    'cost_price': 15.00,
    'selling_price': 37.50,
    'margin_percent': 60.00,
    'image_urls': ['url1', 'url2'],
    'variants': [],
    'inventory_count': 100
})
```

### Create Order

```python
order_id = db.create_order(store_id, {
    'order_id': 'WC-1001',
    'customer_email': 'customer@example.com',
    'total_amount': 49.99,
    'payment_status': 'completed'
})
```

## Brand Asset Generation API

### Generate Complete Brand Package

```python
from brand_generator import BrandAssetGenerator

generator = BrandAssetGenerator()

assets = generator.generate_all_assets(
    brand_name='FitPro',
    niche='fitness',
    color_preference='modern',
    auto_logo=True
)
```

**Response:**

```python
{
    'brand_variations': [
        'FitPro',
        'FitPro Shop',
        'FitProShop',
        'The FitPro',
        'fitpro',
        'getfitpro',
        'myfitpro'
    ],
    'color_palette': ['#2C3E50', '#E74C3C', '#ECF0F1', '#3498DB'],
    'logo_url': './brand_assets/logo_fitpro.svg',
    'tagline': 'Elevate Your Fitness Experience',
    'brand_voice': 'Tone: motivational, energetic, empowering...'
}
```

### Generate Logo Only

```python
# Simple SVG logo
logo_path = generator.generate_logo_simple(
    brand_name='FitPro',
    color_palette=['#2C3E50', '#E74C3C'],
    output_path='./logo.svg'
)

# AI-generated logo (requires API key)
logo_path = generator.generate_logo_via_api(
    brand_name='FitPro',
    niche='fitness',
    color_scheme='modern'
)
```

## Product Import API

### Import Products

```python
from product_importer import ProductImporter

importer = ProductImporter(wc_auth=('consumer_key', 'consumer_secret'))

products = importer.import_products(
    source='cj',
    niche='fitness',
    count=10
)
```

### Process Single Product

```python
processed = importer.process_product(
    raw_product={
        'id': 'CJ-12345',
        'title': 'yoga mat premium quality eco friendly',
        'description': 'Original description...',
        'cost_price': 15.00,
        'images': ['url1', 'url2'],
        'variants': [],
        'inventory': 100
    },
    niche='fitness'
)
```

**Response:**

```python
{
    'supplier_id': 'CJ-12345',
    'title': 'Premium Yoga Mat - Fitness',
    'description': 'Enhanced description with features...',
    'cost_price': 15.00,
    'selling_price': 37.50,
    'margin_percent': 60.00,
    'image_urls': ['compressed_url1', 'compressed_url2'],
    'variants': [],
    'inventory_count': 100,
    'sku': 'SKU-CJ-12345'
}
```

### Bulk Import to WooCommerce

```python
results = importer.bulk_import(
    source='cj',
    niche='fitness',
    wc_api_base='https://yoursite.com/wp-json/wc/v3',
    count=10
)
```

**Response:**

```python
{
    'imported': 8,
    'failed': 2,
    'product_ids': [101, 102, 103, 104, 105, 106, 107, 108],
    'errors': ['Failed to upload: Product A', 'Failed to upload: Product B']
}
```

## Payment Gateway API

### Setup Payment Gateway

```python
from payment_gateways import PaymentGatewayManager

payment_manager = PaymentGatewayManager()

result = payment_manager.setup_gateway(
    gateway_name='stripe',
    country='US',
    store_id=1
)
```

**Response:**

```python
{
    'success': True,
    'gateway': 'stripe',
    'test_transaction_id': 'pi_test_1234567890',
    'config': {
        'publishable_key': 'pk_test_...',
        'webhook_endpoint': '/webhooks/stripe'
    },
    'error': None
}
```

### Create Payment (Stripe)

```python
gateway = payment_manager.get_gateway('stripe')

result = gateway.create_payment(
    amount=49.99,
    currency='USD',
    metadata={'order_id': 'WC-1001'}
)
```

**Response:**

```python
{
    'success': True,
    'payment_id': 'pi_1234567890',
    'client_secret': 'pi_1234567890_secret_abcd',
    'status': 'requires_payment_method'
}
```

### Verify Payment

```python
result = gateway.verify_payment('pi_1234567890')
```

**Response:**

```python
{
    'success': True,
    'status': 'succeeded',
    'amount': 49.99,
    'currency': 'usd'
}
```

## Automation Engine API

### Trigger Event

```python
from automation_engine import AutomationEngine
from database import Database
from config import CONFIG

db = Database(CONFIG.DB_PATH)
automation = AutomationEngine(db, store_id=1)

result = automation.trigger_event('new_order', {
    'order_id': 'WC-1001',
    'customer_email': 'customer@example.com',
    'total_amount': 49.99,
    'payment_status': 'completed',
    'supplier_id': 'CJ-12345'
})
```

**Response:**

```python
{
    'success': True,
    'actions_completed': [
        'order_saved',
        'supplier_notified',
        'confirmation_sent'
    ]
}
```

### Available Events

| Event | Data Required | Actions Triggered |
|-------|---------------|-------------------|
| `new_order` | order_id, customer_email, total_amount | Save order, notify supplier, send confirmation |
| `abandoned_cart` | cart_token, customer_email, total_value | Save cart, schedule recovery email |
| `payment_failed` | order_id, amount, reason, customer_email | Notify admin, send retry link |
| `inventory_low` | product_name, quantity | Alert admin |
| `order_shipped` | order_id, customer_email, tracking_number | Send shipping notification |

## Analytics API

### Setup Analytics

```python
from analytics import AnalyticsManager

analytics = AnalyticsManager()

result = analytics.setup_analytics('yourdomain.com')
```

**Response:**

```python
{
    'success': True,
    'google_analytics': True,
    'meta_pixel': True,
    'tracking_code': '<!-- Analytics Tracking Code -->...'
}
```

### Track Events

```python
# Track purchase
analytics.track_purchase({
    'order_id': 'WC-1001',
    'total_amount': 49.99,
    'currency': 'USD',
    'items': [...]
})

# Track add to cart
analytics.track_add_to_cart({
    'product_id': '101',
    'product_name': 'Yoga Mat',
    'price': 37.50,
    'currency': 'USD'
})
```

### Get Performance Metrics

```python
from analytics import PerformanceAnalytics

perf = PerformanceAnalytics(db, store_id=1)

metrics = perf.get_sales_metrics('2024-01-01', '2024-01-31')
```

**Response:**

```python
{
    'total_orders': 150,
    'total_revenue': 7498.50,
    'avg_order_value': 49.99,
    'unique_customers': 127
}
```

## Webhook API

### Process Webhook

```python
from webhooks import WebhookProcessor
from database import Database
from config import CONFIG

db = Database(CONFIG.DB_PATH)
processor = WebhookProcessor(db)

result = processor.process_webhook(
    provider='stripe',
    event_type='payment_intent.succeeded',
    payload={
        'id': 'pi_1234567890',
        'amount': 4999,
        'receipt_email': 'customer@example.com'
    }
)
```

### Verify Webhook Signature

```python
is_valid = processor.verify_signature(
    payload=request.data,
    signature=request.headers.get('Stripe-Signature'),
    provider='stripe'
)
```

## Scheduled Jobs API

### Run Jobs Manually

```python
from automation_engine import ScheduledJobs
from database import Database
from config import CONFIG

db = Database(CONFIG.DB_PATH)
jobs = ScheduledJobs(db)

# Run daily jobs
jobs.sync_inventory_daily(store_id=1)
jobs.check_payment_status(store_id=1)
jobs.remove_out_of_stock(store_id=1)

# Run weekly jobs
jobs.update_winning_products_weekly(store_id=1)
jobs.adjust_prices_weekly(store_id=1)

# Run monthly jobs
jobs.backup_store_data_monthly(store_id=1)
jobs.generate_performance_report_monthly(store_id=1)
```

## Error Handling

All API methods follow consistent error handling:

```python
try:
    result = orchestrator.create_store_automated(config)
    if result['success']:
        print(f"Store created: {result['store_id']}")
    else:
        print(f"Errors: {result['errors']}")
except Exception as e:
    print(f"Exception: {str(e)}")
```

## Rate Limiting

- API calls: No limit (local processing)
- Webhook processing: 100/hour per store
- Product imports: 1 per second (to avoid supplier API limits)
- Email sending: 500/day (Gmail SMTP limit)

## Testing

### Unit Tests

```python
# Test store creation
def test_create_store():
    db = Database(':memory:')
    store_id = db.create_store({
        'store_name': 'Test Store',
        'niche': 'test',
        'country': 'US',
        'brand_name': 'Test',
        'currency': 'USD',
        'timezone': 'UTC'
    })
    assert store_id > 0

# Test product pricing
def test_calculate_pricing():
    importer = ProductImporter(None)
    pricing = importer.calculate_pricing(10.00, 2.5)
    assert pricing['selling_price'] == 25.00
    assert pricing['margin_percent'] == 60.00
```

### Integration Tests

```python
# Test full workflow
def test_full_workflow():
    orchestrator = StoreOrchestrator()
    result = orchestrator.create_store_automated({
        'niche': 'test',
        'country': 'US',
        'brand_name': 'TestStore',
        'payment_gateway': 'stripe',
        'product_source': 'manual'
    })
    assert result['success'] == True
    assert result['store_id'] > 0
```
