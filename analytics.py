import requests
from typing import Dict, Any, Optional, List
from config import CONFIG

class AnalyticsManager:
    def __init__(self):
        self.ga_measurement_id = CONFIG.GA_MEASUREMENT_ID
        self.meta_pixel_id = CONFIG.META_PIXEL_ID
    
    def setup_analytics(self, store_domain: str) -> Dict[str, Any]:
        """Setup all analytics integrations"""
        results = {
            'success': True,
            'google_analytics': False,
            'meta_pixel': False,
            'tracking_code': None
        }
        
        # Generate tracking code
        tracking_code = self.generate_tracking_code()
        results['tracking_code'] = tracking_code
        
        # Setup Google Analytics
        if self.ga_measurement_id:
            results['google_analytics'] = True
        
        # Setup Meta Pixel
        if self.meta_pixel_id:
            results['meta_pixel'] = True
        
        return results
    
    def generate_tracking_code(self) -> str:
        """Generate unified tracking code snippet"""
        code = "<!-- Analytics Tracking Code -->\n"
        
        # Google Analytics 4
        if self.ga_measurement_id:
            code += f"""
<!-- Google Analytics -->
<script async src="https://www.googletagmanager.com/gtag/js?id={self.ga_measurement_id}"></script>
<script>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{self.ga_measurement_id}', {{
    'send_page_view': true,
    'anonymize_ip': true
  }});
</script>
"""
        
        # Meta Pixel
        if self.meta_pixel_id:
            code += f"""
<!-- Meta Pixel Code -->
<script>
  !function(f,b,e,v,n,t,s)
  {{if(f.fbq)return;n=f.fbq=function(){{n.callMethod?
  n.callMethod.apply(n,arguments):n.queue.push(arguments)}};
  if(!f._fbq)f._fbq=n;n.push=n;n.loaded=!0;n.version='2.0';
  n.queue=[];t=b.createElement(e);t.async=!0;
  t.src=v;s=b.getElementsByTagName(e)[0];
  s.parentNode.insertBefore(t,s)}}(window, document,'script',
  'https://connect.facebook.net/en_US/fbevents.js');
  fbq('init', '{self.meta_pixel_id}');
  fbq('track', 'PageView');
</script>
<noscript>
  <img height="1" width="1" style="display:none"
       src="https://www.facebook.com/tr?id={self.meta_pixel_id}&ev=PageView&noscript=1"/>
</noscript>
"""
        
        return code
    
    def track_event(self, event_name: str, event_data: Dict[str, Any]):
        """Track custom event"""
        # Google Analytics event tracking
        if self.ga_measurement_id:
            self._send_ga_event(event_name, event_data)
        
        # Meta Pixel event tracking
        if self.meta_pixel_id:
            self._send_meta_event(event_name, event_data)
    
    def _send_ga_event(self, event_name: str, params: Dict[str, Any]) -> bool:
        """Send event to Google Analytics via Measurement Protocol"""
        if not self.ga_measurement_id:
            return False
        
        # GA4 Measurement Protocol endpoint
        url = f"https://www.google-analytics.com/mp/collect?measurement_id={self.ga_measurement_id}&api_secret=YOUR_API_SECRET"
        
        payload = {
            "client_id": params.get('client_id', 'anonymous'),
            "events": [{
                "name": event_name,
                "params": params
            }]
        }
        
        try:
            response = requests.post(url, json=payload, timeout=10)
            return response.status_code == 204
        except Exception as e:
            print(f"GA event tracking failed: {e}")
            return False
    
    def _send_meta_event(self, event_name: str, event_data: Dict[str, Any]) -> bool:
        """Send server-side event to Meta Pixel"""
        if not self.meta_pixel_id:
            return False
        
        # Meta Conversions API endpoint
        url = f"https://graph.facebook.com/v18.0/{self.meta_pixel_id}/events"
        
        # This requires an access token - placeholder implementation
        print(f"Meta Pixel event: {event_name} - {event_data}")
        return True
    
    def track_purchase(self, order_data: Dict[str, Any]):
        """Track purchase conversion"""
        event_data = {
            'transaction_id': order_data['order_id'],
            'value': order_data['total_amount'],
            'currency': order_data.get('currency', 'USD'),
            'items': order_data.get('items', [])
        }
        
        self.track_event('purchase', event_data)
    
    def track_add_to_cart(self, product_data: Dict[str, Any]):
        """Track add to cart event"""
        event_data = {
            'item_id': product_data['product_id'],
            'item_name': product_data['product_name'],
            'value': product_data['price'],
            'currency': product_data.get('currency', 'USD')
        }
        
        self.track_event('add_to_cart', event_data)
    
    def track_page_view(self, page_data: Dict[str, Any]):
        """Track page view"""
        event_data = {
            'page_title': page_data.get('title', ''),
            'page_location': page_data.get('url', ''),
            'page_path': page_data.get('path', '')
        }
        
        self.track_event('page_view', event_data)
    
    def generate_conversion_tracking_code(self) -> str:
        """Generate ecommerce conversion tracking code"""
        code = """
<script>
// Ecommerce Tracking
function trackPurchase(orderId, total, currency, items) {
"""
        
        if self.ga_measurement_id:
            code += f"""
  // Google Analytics
  gtag('event', 'purchase', {{
    transaction_id: orderId,
    value: total,
    currency: currency,
    items: items
  }});
"""
        
        if self.meta_pixel_id:
            code += """
  // Meta Pixel
  fbq('track', 'Purchase', {
    value: total,
    currency: currency,
    contents: items,
    content_type: 'product'
  });
"""
        
        code += """
}

function trackAddToCart(productId, productName, price) {
"""
        
        if self.ga_measurement_id:
            code += """
  gtag('event', 'add_to_cart', {
    items: [{
      item_id: productId,
      item_name: productName,
      price: price
    }]
  });
"""
        
        if self.meta_pixel_id:
            code += """
  fbq('track', 'AddToCart', {
    content_ids: [productId],
    content_name: productName,
    value: price,
    currency: 'USD'
  });
"""
        
        code += """
}
</script>
"""
        
        return code


class PerformanceAnalytics:
    def __init__(self, db, store_id: int):
        self.db = db
        self.store_id = store_id
    
    def get_sales_metrics(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Get sales performance metrics"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                COUNT(*) as total_orders,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_order_value,
                COUNT(DISTINCT customer_email) as unique_customers
            FROM orders
            WHERE store_id = ? 
            AND created_at BETWEEN ? AND ?
            AND payment_status = 'completed'
        ''', (self.store_id, start_date, end_date))
        
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return {
                'total_orders': row[0] or 0,
                'total_revenue': row[1] or 0.0,
                'avg_order_value': row[2] or 0.0,
                'unique_customers': row[3] or 0
            }
        
        return {}
    
    def get_product_performance(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get top performing products"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT 
                title,
                selling_price,
                margin_percent,
                inventory_count,
                status
            FROM products
            WHERE store_id = ?
            ORDER BY margin_percent DESC
            LIMIT ?
        ''', (self.store_id, limit))
        
        products = []
        for row in cursor.fetchall():
            products.append({
                'title': row[0],
                'price': row[1],
                'margin': row[2],
                'inventory': row[3],
                'status': row[4]
            })
        
        conn.close()
        return products
    
    def get_conversion_rate(self, start_date: str, end_date: str) -> float:
        """Calculate conversion rate"""
        # Placeholder - requires visitor tracking
        return 2.5  # Mock 2.5% conversion rate
    
    def generate_report(self, start_date: str, end_date: str) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        return {
            'period': {'start': start_date, 'end': end_date},
            'sales_metrics': self.get_sales_metrics(start_date, end_date),
            'top_products': self.get_product_performance(5),
            'conversion_rate': self.get_conversion_rate(start_date, end_date)
        }
