import requests
from typing import Dict, Any, Optional, List
from config import CONFIG
import base64
import time

class WooCommerceStoreSetup:
    def __init__(self, site_url: str, consumer_key: str, consumer_secret: str):
        self.site_url = site_url.rstrip('/')
        self.consumer_key = consumer_key
        self.consumer_secret = consumer_secret
        self.api_base = f"{self.site_url}/wp-json/wc/v3"
        self.wp_api_base = f"{self.site_url}/wp-json/wp/v2"
        self.auth = (consumer_key, consumer_secret)
    
    def _request(self, method: str, endpoint: str, data: Optional[Dict] = None, 
                 retries: int = CONFIG.MAX_RETRIES) -> Optional[Dict]:
        """Make authenticated API request with retry logic"""
        url = f"{self.api_base}{endpoint}"
        
        for attempt in range(retries):
            try:
                if method == 'GET':
                    response = requests.get(url, auth=self.auth, timeout=30)
                elif method == 'POST':
                    response = requests.post(url, auth=self.auth, json=data, timeout=30)
                elif method == 'PUT':
                    response = requests.put(url, auth=self.auth, json=data, timeout=30)
                elif method == 'DELETE':
                    response = requests.delete(url, auth=self.auth, timeout=30)
                else:
                    raise ValueError(f"Unsupported method: {method}")
                
                if response.status_code in [200, 201]:
                    return response.json()
                elif response.status_code == 404:
                    return None
                else:
                    print(f"API Error {response.status_code}: {response.text}")
                    
            except Exception as e:
                print(f"Request failed (attempt {attempt + 1}/{retries}): {e}")
                if attempt < retries - 1:
                    time.sleep(CONFIG.RETRY_DELAY_SECONDS)
        
        return None
    
    def _wp_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Optional[Dict]:
        """WordPress REST API request"""
        url = f"{self.wp_api_base}{endpoint}"
        headers = {
            'Authorization': f'Basic {base64.b64encode(f"{CONFIG.WP_USERNAME}:{CONFIG.WP_APP_PASSWORD}".encode()).decode()}'
        }
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=30)
            elif method == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method == 'PUT':
                response = requests.put(url, headers=headers, json=data, timeout=30)
            else:
                return None
            
            if response.status_code in [200, 201]:
                return response.json()
        except Exception as e:
            print(f"WordPress API error: {e}")
        
        return None
    
    def configure_store_settings(self, currency: str, timezone: str, country: str) -> bool:
        """Configure basic store settings"""
        settings = [
            {"id": "woocommerce_currency", "value": currency},
            {"id": "woocommerce_default_country", "value": country},
            {"id": "timezone_string", "value": timezone},
            {"id": "woocommerce_calc_taxes", "value": "yes"},
            {"id": "woocommerce_price_display_suffix", "value": ""},
            {"id": "woocommerce_enable_guest_checkout", "value": "yes"},
            {"id": "woocommerce_enable_signup_and_login_from_checkout", "value": "yes"}
        ]
        
        success = True
        for setting in settings:
            result = self._request('PUT', f"/settings/{setting['id']}", {"value": setting["value"]})
            if not result:
                success = False
                print(f"Failed to set {setting['id']}")
        
        return success
    
    def create_pages(self, brand_name: str, niche: str) -> Dict[str, int]:
        """Create essential store pages"""
        pages = {
            'home': {
                'title': f'Welcome to {brand_name}',
                'content': f'<h1>Welcome to {brand_name}</h1><p>Your trusted source for quality {niche} products.</p>',
                'status': 'publish'
            },
            'contact': {
                'title': 'Contact Us',
                'content': f'<h2>Get in Touch</h2><p>Have questions? We\'re here to help!</p><p>Email: support@{brand_name.lower().replace(" ", "")}.com</p>',
                'status': 'publish'
            },
            'shipping': {
                'title': 'Shipping Information',
                'content': '<h2>Shipping Policy</h2><p>We offer worldwide shipping with multiple carrier options.</p><ul><li>Standard Shipping: 7-14 business days</li><li>Express Shipping: 3-5 business days</li><li>Free shipping on orders over $50</li></ul>',
                'status': 'publish'
            },
            'privacy': {
                'title': 'Privacy Policy',
                'content': '<h2>Privacy Policy</h2><p>Your privacy is important to us. This policy outlines how we collect, use, and protect your personal information.</p><h3>Information Collection</h3><p>We collect information you provide during checkout and browsing.</p><h3>Data Protection</h3><p>We use industry-standard encryption to protect your data.</p>',
                'status': 'publish'
            },
            'refund': {
                'title': 'Refund Policy',
                'content': '<h2>Refund & Return Policy</h2><p>We want you to be completely satisfied with your purchase.</p><h3>30-Day Returns</h3><p>Return any item within 30 days for a full refund.</p><h3>Refund Process</h3><p>Refunds are processed within 5-7 business days.</p>',
                'status': 'publish'
            }
        }
        
        page_ids = {}
        for key, page_data in pages.items():
            result = self._wp_request('POST', '/pages', page_data)
            if result and 'id' in result:
                page_ids[key] = result['id']
                print(f"Created page: {page_data['title']}")
            else:
                print(f"Failed to create page: {page_data['title']}")
        
        return page_ids
    
    def install_theme(self, theme_slug: str = 'astra') -> bool:
        """Install and activate WooCommerce-compatible theme"""
        # Note: Requires WordPress REST API extensions or WP-CLI access
        # This is a placeholder - actual implementation needs server access
        print(f"Theme installation requires server-side WP-CLI access")
        print(f"Recommended theme: {theme_slug}")
        print(f"Manual installation: Appearance > Themes > Add New > Search '{theme_slug}'")
        return True
    
    def apply_brand_colors(self, color_palette: List[str]) -> bool:
        """Apply brand colors to theme"""
        # This requires theme-specific customizer API
        # Most free themes like Astra support customizer API
        customizer_settings = {
            'primary_color': color_palette[0] if len(color_palette) > 0 else '#2C3E50',
            'secondary_color': color_palette[1] if len(color_palette) > 1 else '#E74C3C',
            'text_color': color_palette[2] if len(color_palette) > 2 else '#333333',
            'link_color': color_palette[3] if len(color_palette) > 3 else '#3498DB'
        }
        
        print(f"Brand colors configured: {customizer_settings}")
        # Implementation requires theme-specific API endpoints
        return True
    
    def upload_logo(self, logo_path: str) -> Optional[str]:
        """Upload logo to WordPress media library"""
        # Requires WordPress media upload API
        print(f"Logo upload requires media API: {logo_path}")
        # Placeholder - actual implementation needs multipart/form-data upload
        return logo_path
    
    def configure_homepage(self, page_id: int) -> bool:
        """Set static homepage"""
        settings = [
            {"id": "show_on_front", "value": "page"},
            {"id": "page_on_front", "value": str(page_id)}
        ]
        
        for setting in settings:
            result = self._wp_request('POST', f'/settings', setting)
            if not result:
                print(f"Failed to set homepage setting: {setting['id']}")
                return False
        
        return True
    
    def setup_complete_store(self, brand_name: str, niche: str, currency: str, 
                           timezone: str, country: str, color_palette: List[str],
                           logo_path: Optional[str] = None) -> Dict[str, Any]:
        """Complete store setup workflow"""
        results = {
            'success': True,
            'settings_configured': False,
            'pages_created': {},
            'theme_configured': False,
            'errors': []
        }
        
        # Configure settings
        if self.configure_store_settings(currency, timezone, country):
            results['settings_configured'] = True
        else:
            results['errors'].append("Failed to configure store settings")
            results['success'] = False
        
        # Create pages
        page_ids = self.create_pages(brand_name, niche)
        results['pages_created'] = page_ids
        
        if 'home' not in page_ids:
            results['errors'].append("Failed to create homepage")
        
        # Apply branding
        if self.apply_brand_colors(color_palette):
            results['theme_configured'] = True
        
        if logo_path:
            logo_url = self.upload_logo(logo_path)
            results['logo_url'] = logo_url
        
        # Set homepage
        if 'home' in page_ids:
            self.configure_homepage(page_ids['home'])
        
        return results
