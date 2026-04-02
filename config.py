from dotenv import load_dotenv
load_dotenv()

import os
import sys
import re
from dataclasses import dataclass
from typing import Dict, List, Optional

@dataclass
class SystemConfig:
    # Environment mode
    ENV = os.getenv("ENV", "dev").lower()  # dev, test, prod
    DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"
    
    # Free alternatives to Shopify API
    PLATFORM = "WooCommerce"  # Free, open-source
    WORDPRESS_API_URL = os.getenv("WP_API_URL", "")
    WP_USERNAME = os.getenv("WP_USER", "")
    WP_APP_PASSWORD = os.getenv("WP_APP_PASSWORD", "")
    
    # Free AI APIs
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")  # Free tier available
    STABILITY_API_KEY = os.getenv("STABILITY_API_KEY", "")  # Free tier
    
    # Free payment gateways
    STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
    STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY", "")
    PAYPAL_CLIENT_ID = os.getenv("PAYPAL_CLIENT_ID", "")
    PAYPAL_SECRET = os.getenv("PAYPAL_SECRET", "")
    RAZORPAY_KEY = os.getenv("RAZORPAY_KEY", "")
    RAZORPAY_SECRET = os.getenv("RAZORPAY_SECRET", "")
    
    # Free supplier APIs
    ALIEXPRESS_API_KEY = os.getenv("ALIEXPRESS_API_KEY", "")
    CJDROPSHIPPING_API_KEY = os.getenv("CJ_API_KEY", "")
    
    # Free analytics
    GA_MEASUREMENT_ID = os.getenv("GA_MEASUREMENT_ID", "")
    META_PIXEL_ID = os.getenv("META_PIXEL_ID", "")
    
    # Free email service
    SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USER = os.getenv("SMTP_USER", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    
    # Free image optimization
    TINIFY_API_KEY = os.getenv("TINIFY_API_KEY", "")  # Free tier: 500/month
    
    # Database
    DB_PATH = "./store_automation.db"
    
    # Pricing rules
    PRICE_MULTIPLIER = 2.5
    MIN_MARGIN_PERCENT = 30
    
    # Automation intervals
    INVENTORY_SYNC_HOURS = 24
    CART_RECOVERY_HOURS = 1
    BACKUP_DAYS = 30
    
    # Retry configuration
    MAX_RETRIES = 3  
    RETRY_DELAY_SECONDS = 5
    
    # Webhook endpoints
    WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")
    WEBHOOK_PORT = int(os.getenv("WEBHOOK_PORT", "8080"))

CONFIG = SystemConfig()

PAYMENT_COUNTRY_MAP = {
    "US": ["stripe", "paypal"],
    "CA": ["stripe", "paypal"],
    "GB": ["stripe", "paypal"],
    "AU": ["stripe", "paypal"],
    "IN": ["razorpay", "paypal"],
    "SG": ["stripe", "paypal"],
    "AE": ["stripe", "paypal"],
    "DEFAULT": ["paypal"]
}

CURRENCY_MAP = {
    "US": "USD",
    "CA": "CAD",
    "GB": "GBP",
    "AU": "AUD",
    "IN": "INR",
    "SG": "SGD",
    "AE": "AED",
    "EU": "EUR"
}

TIMEZONE_MAP = {
    "US": "America/New_York",
    "CA": "America/Toronto",
    "GB": "Europe/London",
    "AU": "Australia/Sydney",
    "IN": "Asia/Kolkata",
    "SG": "Asia/Singapore",
    "AE": "Asia/Dubai"
}

FREE_WP_THEMES = [
    "Astra",
    "OceanWP", 
    "Kadence",
    "Neve",
    "Blocksy"
]

COLOR_PALETTES = {
    "modern": ["#2C3E50", "#E74C3C", "#ECF0F1", "#3498DB"],
    "minimal": ["#000000", "#FFFFFF", "#F5F5F5", "#333333"],
    "vibrant": ["#FF6B6B", "#4ECDC4", "#45B7D1", "#FFA07A"],
    "nature": ["#2ECC71", "#27AE60", "#F39C12", "#E67E22"],
    "tech": ["#3498DB", "#2C3E50", "#9B59B6", "#1ABC9C"],
    "luxury": ["#8E44AD", "#2C3E50", "#D4AF37", "#ECF0F1"]
}

def mask_sensitive(value: str, visible_chars: int = 4) -> str:
    """Mask sensitive values for logging - PRODUCTION SAFETY"""
    if not value or len(value) <= visible_chars:
        return "***"
    return value[:visible_chars] + ("*" * (len(value) - visible_chars))

def validate_config() -> List[str]:
    """Validate configuration at startup - FAIL FAST"""
    errors = []
    
    # Validate environment
    if CONFIG.ENV not in ["dev", "test", "prod"]:
        errors.append(f"Invalid ENV '{CONFIG.ENV}'. Must be: dev, test, or prod")
    
    # In production mode, require critical configs
    if CONFIG.ENV == "prod" and not CONFIG.DRY_RUN:
        # WordPress/WooCommerce required for store creation
        if not CONFIG.WORDPRESS_API_URL:
            errors.append("WP_API_URL is required in production mode")
        if CONFIG.WORDPRESS_API_URL and not CONFIG.WORDPRESS_API_URL.startswith("http"):
            errors.append(f"WP_API_URL must start with http:// or https://")
        
        # At least one payment gateway required
        has_payment = any([
            CONFIG.STRIPE_SECRET_KEY,
            CONFIG.PAYPAL_CLIENT_ID,
            CONFIG.RAZORPAY_KEY
        ])
        if not has_payment:
            errors.append("At least one payment gateway must be configured in production")
        
        # Email required for notifications
        if not CONFIG.SMTP_USER:
            errors.append("SMTP_USER is required for email notifications in production")
    
    # Validate API keys format if provided
    if CONFIG.STRIPE_SECRET_KEY and not CONFIG.STRIPE_SECRET_KEY.startswith("sk_"):
        errors.append("STRIPE_SECRET_KEY appears invalid (should start with sk_)")
    
    if CONFIG.STRIPE_PUBLISHABLE_KEY and not CONFIG.STRIPE_PUBLISHABLE_KEY.startswith("pk_"):
        errors.append("STRIPE_PUBLISHABLE_KEY appears invalid (should start with pk_)")
    
    # Validate email format if provided
    if CONFIG.SMTP_USER:
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, CONFIG.SMTP_USER):
            errors.append(f"SMTP_USER '{CONFIG.SMTP_USER}' is not a valid email address")
    
    # Validate numeric configs
    try:
        if CONFIG.SMTP_PORT <= 0 or CONFIG.SMTP_PORT > 65535:
            errors.append(f"SMTP_PORT must be between 1-65535, got {CONFIG.SMTP_PORT}")
    except (ValueError, TypeError):
        errors.append(f"SMTP_PORT must be a valid number")
    
    try:
        if CONFIG.WEBHOOK_PORT <= 0 or CONFIG.WEBHOOK_PORT > 65535:
            errors.append(f"WEBHOOK_PORT must be between 1-65535, got {CONFIG.WEBHOOK_PORT}")
    except (ValueError, TypeError):
        errors.append(f"WEBHOOK_PORT must be a valid number")
    
    return errors

def print_config_errors_and_exit(errors: List[str]):
    """Print validation errors and exit - PRODUCTION SAFETY"""
    print("\n" + "="*60)
    print("CONFIGURATION ERROR - Cannot Start")
    print("="*60)
    for i, error in enumerate(errors, 1):
        print(f"{i}. {error}")
    print("="*60)
    print("\nPlease check your .env file and environment variables.")
    print("See .env.example for required configuration.\n")
    sys.exit(1)
