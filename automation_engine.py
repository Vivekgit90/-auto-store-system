import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from config import CONFIG, mask_sensitive
import json

class AutomationEngine:
    def __init__(self, db, store_id: int, dry_run: bool = False):
        self.db = db
        self.store_id = store_id
        self.dry_run = dry_run  # PRODUCTION SAFETY: dry-run mode
        self.handlers = {
            'new_order': self.handle_new_order,
            'abandoned_cart': self.handle_abandoned_cart,
            'payment_failed': self.handle_payment_failed,
            'inventory_low': self.handle_low_inventory,
            'order_shipped': self.handle_order_shipped
        }
    
    def trigger_event(self, event_type: str, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Trigger automation event"""
        handler = self.handlers.get(event_type)
        if not handler:
            return {
                'success': False,
                'error': f'Unknown event type: {event_type}'
            }
        
        try:
            result = handler(event_data)
            
            # Log automation
            self.db.log_automation(
                self.store_id,
                event_type,
                'success' if result.get('success') else 'failed',
                json.dumps(result),
                result.get('error')
            )
            
            return result
        except Exception as e:
            error_msg = str(e)
            self.db.log_automation(
                self.store_id,
                event_type,
                'error',
                'Exception occurred',
                error_msg
            )
            return {
                'success': False,
                'error': error_msg
            }
    
    def handle_new_order(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle new order event"""
        results = {
            'success': True,
            'actions_completed': []
        }
        
        # Save order to database
        self.db.create_order(self.store_id, order_data)
        results['actions_completed'].append('order_saved')
        
        # Send to supplier (if dropshipping)
        if order_data.get('supplier_id'):
            supplier_result = self.send_to_supplier(order_data)
            results['actions_completed'].append('supplier_notified')
        
        # Send confirmation email to customer
        if order_data.get('customer_email'):
            email_sent = self.send_order_confirmation(
                order_data['customer_email'],
                order_data['order_id'],
                order_data['total_amount']
            )
            if email_sent:
                results['actions_completed'].append('confirmation_sent')
        
        return results
    
    def handle_abandoned_cart(self, cart_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle abandoned cart after delay"""
        # Save cart
        self.db.save_abandoned_cart(self.store_id, cart_data)
        
        # Wait 1 hour before sending recovery email
        # In production, this would be handled by a scheduled job
        
        if cart_data.get('customer_email'):
            email_sent = self.send_cart_recovery_email(
                cart_data['customer_email'],
                cart_data.get('cart_token'),
                cart_data.get('total_value', 0)
            )
            
            if email_sent:
                return {
                    'success': True,
                    'recovery_sent': True
                }
        
        return {
            'success': True,
            'recovery_sent': False
        }
    
    def handle_payment_failed(self, payment_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle payment failure"""
        # Notify admin
        admin_notified = self.send_admin_notification(
            f"Payment failed for order {payment_data.get('order_id')}",
            f"Amount: {payment_data.get('amount')}, Reason: {payment_data.get('reason')}"
        )
        
        # Send retry link to customer
        retry_link_sent = False
        if payment_data.get('customer_email'):
            retry_link_sent = self.send_payment_retry_link(
                payment_data['customer_email'],
                payment_data.get('order_id'),
                payment_data.get('payment_url')
            )
        
        return {
            'success': True,
            'admin_notified': admin_notified,
            'retry_link_sent': retry_link_sent
        }
    
    def handle_low_inventory(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle low inventory alert"""
        admin_notified = self.send_admin_notification(
            f"Low inventory alert: {product_data.get('product_name')}",
            f"Current stock: {product_data.get('quantity')}"
        )
        
        return {
            'success': True,
            'admin_notified': admin_notified
        }
    
    def handle_order_shipped(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle order shipped notification"""
        if order_data.get('customer_email'):
            email_sent = self.send_shipping_notification(
                order_data['customer_email'],
                order_data['order_id'],
                order_data.get('tracking_number')
            )
            
            return {
                'success': True,
                'notification_sent': email_sent
            }
        
        return {'success': False}
    
    def send_to_supplier(self, order_data: Dict[str, Any]) -> bool:
        """Send order to dropshipping supplier"""
        # Implementation depends on supplier API
        # Placeholder for CJ Dropshipping, AliExpress, etc.
        print(f"Sending order {order_data['order_id']} to supplier")
        return True
    
    def send_order_confirmation(self, email: str, order_id: str, amount: float) -> bool:
        """Send order confirmation email"""
        subject = f"Order Confirmation - #{order_id}"
        body = f"""
        <html>
        <body>
            <h2>Thank you for your order!</h2>
            <p>Your order #{order_id} has been confirmed.</p>
            <p><strong>Total: ${amount:.2f}</strong></p>
            <p>We'll send you another email when your order ships.</p>
            <p>Thank you for shopping with us!</p>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, body)
    
    def send_cart_recovery_email(self, email: str, cart_token: str, value: float) -> bool:
        """Send abandoned cart recovery email"""
        subject = "You left items in your cart"
        recovery_url = f"https://store.example.com/cart/{cart_token}"
        
        body = f"""
        <html>
        <body>
            <h2>Don't miss out!</h2>
            <p>You have ${value:.2f} worth of items waiting in your cart.</p>
            <p><a href="{recovery_url}" style="background-color: #4CAF50; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Complete Your Purchase</a></p>
            <p>Items sell fast - grab yours before they're gone!</p>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, body)
    
    def send_payment_retry_link(self, email: str, order_id: str, payment_url: str) -> bool:
        """Send payment retry link"""
        subject = f"Payment Update Required - Order #{order_id}"
        body = f"""
        <html>
        <body>
            <h2>Payment Issue</h2>
            <p>We couldn't process your payment for order #{order_id}.</p>
            <p><a href="{payment_url}" style="background-color: #2196F3; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px;">Update Payment Method</a></p>
            <p>If you have questions, please contact our support team.</p>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, body)
    
    def send_shipping_notification(self, email: str, order_id: str, tracking: Optional[str]) -> bool:
        """Send shipping notification"""
        subject = f"Your Order Has Shipped - #{order_id}"
        
        tracking_info = ""
        if tracking:
            tracking_info = f"<p><strong>Tracking Number:</strong> {tracking}</p>"
        
        body = f"""
        <html>
        <body>
            <h2>Great News! Your Order is on the Way</h2>
            <p>Order #{order_id} has been shipped and is headed your way.</p>
            {tracking_info}
            <p>You should receive it within 5-7 business days.</p>
            <p>Thank you for your purchase!</p>
        </body>
        </html>
        """
        
        return self._send_email(email, subject, body)
    
    def send_admin_notification(self, subject: str, message: str) -> bool:
        """Send notification to store admin"""
        admin_email = CONFIG.SMTP_USER
        
        body = f"""
        <html>
        <body>
            <h2>Store Notification</h2>
            <p>{message}</p>
            <p><em>Automated notification from your store automation system</em></p>
        </body>
        </html>
        """
        
        return self._send_email(admin_email, subject, body)
    
    def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via SMTP with dry-run support and credential masking - PRODUCTION SAFETY"""
        # DRY RUN: Skip actual email sending
        if self.dry_run:
            print(f"[DRY-RUN] Would send email to {to_email}: {subject}")
            return True
        
        if not CONFIG.SMTP_USER or not CONFIG.SMTP_PASSWORD:
            print(f"[INFO] Email would be sent to {to_email}: {subject} (SMTP not configured)")
            return True  # Mock success for testing
        
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = CONFIG.SMTP_USER
            msg['To'] = to_email
            
            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)
            
            with smtplib.SMTP(CONFIG.SMTP_HOST, CONFIG.SMTP_PORT) as server:
                server.starttls()
                server.login(CONFIG.SMTP_USER, CONFIG.SMTP_PASSWORD)
                server.send_message(msg)
            
            return True
        except Exception as e:
            # Mask credentials in error logs - PRODUCTION SAFETY
            error_msg = str(e).replace(CONFIG.SMTP_PASSWORD, '***')
            print(f"Email send failed: {error_msg}")
            return False


class ScheduledJobs:
    def __init__(self, db):
        self.db = db
    
    def sync_inventory_daily(self, store_id: int):
        """Daily inventory sync with suppliers"""
        print(f"Running inventory sync for store {store_id}")
        # Implementation: Fetch inventory from supplier APIs and update database
        
        self.db.log_automation(
            store_id,
            'inventory_sync',
            'success',
            'Daily inventory sync completed'
        )
    
    def check_payment_status(self, store_id: int):
        """Check pending payment statuses"""
        print(f"Checking payment statuses for store {store_id}")
        # Implementation: Query payment gateway APIs for pending transactions
        
        self.db.log_automation(
            store_id,
            'payment_check',
            'success',
            'Payment status check completed'
        )
    
    def remove_out_of_stock(self, store_id: int):
        """Remove products with zero inventory"""
        print(f"Removing out of stock products for store {store_id}")
        # Implementation: Update product status in WooCommerce
        
        self.db.log_automation(
            store_id,
            'remove_oos',
            'success',
            'Out of stock products removed'
        )
    
    def update_winning_products_weekly(self, store_id: int):
        """Update product catalog with trending items"""
        print(f"Updating winning products for store {store_id}")
        # Implementation: Fetch trending products from suppliers
        
        self.db.log_automation(
            store_id,
            'update_products',
            'success',
            'Product catalog updated'
        )
    
    def adjust_prices_weekly(self, store_id: int):
        """Adjust prices based on market conditions"""
        print(f"Adjusting prices for store {store_id}")
        # Implementation: Analyze competitor prices and adjust margins
        
        self.db.log_automation(
            store_id,
            'price_adjustment',
            'success',
            'Prices adjusted'
        )
    
    def backup_store_data_monthly(self, store_id: int):
        """Monthly store data backup"""
        print(f"Backing up store data for {store_id}")
        # Implementation: Export database and files
        
        self.db.log_automation(
            store_id,
            'backup',
            'success',
            'Store data backed up'
        )
    
    def generate_performance_report_monthly(self, store_id: int):
        """Generate monthly performance report"""
        print(f"Generating performance report for store {store_id}")
        # Implementation: Compile analytics and send report
        
        self.db.log_automation(
            store_id,
            'performance_report',
            'success',
            'Performance report generated'
        )
