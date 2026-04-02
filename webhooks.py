from flask import Flask
from flask_cors import CORS
from flask_cors import CORS
import hashlib
import hmac
import json
from typing import Dict, Any, Optional
from config import CONFIG
from automation_engine import AutomationEngine
from database import Database

app = Flask(__name__)
CORS(app)
CORS(app)
db = Database(CONFIG.DB_PATH)

class WebhookProcessor:
    def __init__(self, db: Database):
        self.db = db
        self.secret = CONFIG.WEBHOOK_SECRET
    
    def verify_signature(self, payload: bytes, signature: str, provider: str) -> bool:
        """Verify webhook signature"""
        if provider == 'stripe':
            return self._verify_stripe_signature(payload, signature)
        elif provider == 'paypal':
            return self._verify_paypal_signature(payload, signature)
        elif provider == 'woocommerce':
            return self._verify_woocommerce_signature(payload, signature)
        
        return False
    
    def _verify_stripe_signature(self, payload: bytes, signature: str) -> bool:
        """Verify Stripe webhook signature"""
        if not self.secret:
            return True  # Skip verification in dev mode
        
        try:
            # Stripe sends signature in format: t=timestamp,v1=signature
            parts = dict(item.split('=') for item in signature.split(','))
            timestamp = parts.get('t')
            expected_sig = parts.get('v1')
            
            signed_payload = f"{timestamp}.{payload.decode()}"
            computed_sig = hmac.new(
                self.secret.encode(),
                signed_payload.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(computed_sig, expected_sig)
        except Exception as e:
            print(f"Signature verification failed: {e}")
            return False
    
    def _verify_paypal_signature(self, payload: bytes, signature: str) -> bool:
        """Verify PayPal webhook signature"""
        # PayPal uses a different verification method
        # Placeholder implementation
        return True
    
    def _verify_woocommerce_signature(self, payload: bytes, signature: str) -> bool:
        """Verify WooCommerce webhook signature"""
        if not self.secret:
            return True
        
        computed_sig = hmac.new(
            self.secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(computed_sig, signature)
    
    def process_webhook(self, provider: str, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Process webhook event"""
        # Store webhook for processing
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO webhooks (store_id, event_type, payload)
            VALUES (?, ?, ?)
        ''', (
            payload.get('store_id', 1),  # Default store for demo
            f"{provider}:{event_type}",
            json.dumps(payload)
        ))
        
        webhook_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        # Process immediately
        return self.process_webhook_by_id(webhook_id)
    
    def process_webhook_by_id(self, webhook_id: int) -> Dict[str, Any]:
        """Process stored webhook"""
        conn = self.db.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT store_id, event_type, payload
            FROM webhooks
            WHERE id = ?
        ''', (webhook_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return {'success': False, 'error': 'Webhook not found'}
        
        store_id, event_type, payload_json = row
        payload = json.loads(payload_json)
        
        # Route to appropriate handler
        provider, event = event_type.split(':', 1)
        
        automation = AutomationEngine(self.db, store_id)
        
        if provider == 'stripe':
            result = self._handle_stripe_event(event, payload, automation)
        elif provider == 'paypal':
            result = self._handle_paypal_event(event, payload, automation)
        elif provider == 'woocommerce':
            result = self._handle_woocommerce_event(event, payload, automation)
        else:
            result = {'success': False, 'error': f'Unknown provider: {provider}'}
        
        # Mark as processed
        if result.get('success'):
            self.db.mark_webhook_processed(webhook_id)
        else:
            self.db.increment_webhook_retry(webhook_id)
        
        return result
    
    def _handle_stripe_event(self, event: str, payload: Dict[str, Any], automation: AutomationEngine) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        if event == 'payment_intent.succeeded':
            order_data = {
                'order_id': payload.get('id'),
                'customer_email': payload.get('receipt_email'),
                'total_amount': payload.get('amount', 0) / 100,
                'payment_status': 'completed'
            }
            return automation.trigger_event('new_order', order_data)
        
        elif event == 'payment_intent.payment_failed':
            payment_data = {
                'order_id': payload.get('id'),
                'amount': payload.get('amount', 0) / 100,
                'reason': payload.get('last_payment_error', {}).get('message'),
                'customer_email': payload.get('receipt_email')
            }
            return automation.trigger_event('payment_failed', payment_data)
        
        elif event == 'charge.refunded':
            # Handle refund
            return {'success': True, 'message': 'Refund processed'}
        
        return {'success': True, 'message': 'Event received'}
    
    def _handle_paypal_event(self, event: str, payload: Dict[str, Any], automation: AutomationEngine) -> Dict[str, Any]:
        """Handle PayPal webhook events"""
        if event == 'PAYMENT.CAPTURE.COMPLETED':
            order_data = {
                'order_id': payload.get('resource', {}).get('id'),
                'customer_email': payload.get('resource', {}).get('payer', {}).get('email_address'),
                'total_amount': float(payload.get('resource', {}).get('amount', {}).get('value', 0)),
                'payment_status': 'completed'
            }
            return automation.trigger_event('new_order', order_data)
        
        return {'success': True, 'message': 'Event received'}
    
    def _handle_woocommerce_event(self, event: str, payload: Dict[str, Any], automation: AutomationEngine) -> Dict[str, Any]:
        """Handle WooCommerce webhook events"""
        if event == 'order.created':
            order_data = {
                'order_id': str(payload.get('id')),
                'customer_email': payload.get('billing', {}).get('email'),
                'total_amount': float(payload.get('total', 0)),
                'payment_status': 'pending'
            }
            return automation.trigger_event('new_order', order_data)
        
        elif event == 'order.updated':
            status = payload.get('status')
            if status == 'completed':
                return {'success': True, 'message': 'Order completed'}
        
        return {'success': True, 'message': 'Event received'}


# Flask webhook endpoints
webhook_processor = WebhookProcessor(db)

@app.route('/webhooks/stripe', methods=['POST'])
def stripe_webhook():
    """Stripe webhook endpoint"""
    payload = request.data
    signature = request.headers.get('Stripe-Signature', '')
    
    # Verify signature
    if not webhook_processor.verify_signature(payload, signature, 'stripe'):
        return jsonify({'error': 'Invalid signature'}), 401
    
    try:
        event = json.loads(payload)
        result = webhook_processor.process_webhook(
            'stripe',
            event.get('type'),
            event.get('data', {}).get('object', {})
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/webhooks/paypal', methods=['POST'])
def paypal_webhook():
    """PayPal webhook endpoint"""
    payload = request.data
    signature = request.headers.get('PAYPAL-TRANSMISSION-SIG', '')
    
    try:
        event = request.json
        result = webhook_processor.process_webhook(
            'paypal',
            event.get('event_type'),
            event
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/webhooks/woocommerce', methods=['POST'])
def woocommerce_webhook():
    """WooCommerce webhook endpoint"""
    payload = request.data
    signature = request.headers.get('X-WC-Webhook-Signature', '')
    
    try:
        event = request.json
        event_type = request.headers.get('X-WC-Webhook-Topic', '')
        
        result = webhook_processor.process_webhook(
            'woocommerce',
            event_type,
            event
        )
        
        return jsonify(result), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy'}), 200


def start_webhook_server(port: int = CONFIG.WEBHOOK_PORT):
    """Start webhook listener server"""
    print(f"Starting webhook server on port {port}")
    app.run(host='0.0.0.0', port=port, debug=False)


def process_pending_webhooks():
    """Process any pending webhooks (for retry logic)"""
    pending = db.get_pending_webhooks()
    
    for webhook_id, store_id, event_type, payload, retry_count in pending:
        print(f"Processing webhook {webhook_id} (retry {retry_count})")
        
        try:
            result = webhook_processor.process_webhook_by_id(webhook_id)
            print(f"Webhook {webhook_id} processed: {result}")
        except Exception as e:
            print(f"Webhook {webhook_id} failed: {e}")


if __name__ == '__main__':
    start_webhook_server()
