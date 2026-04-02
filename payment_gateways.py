import stripe
import requests
from typing import Dict, Any, Optional
from config import CONFIG, PAYMENT_COUNTRY_MAP, mask_sensitive

class PaymentGatewayManager:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run  # PRODUCTION SAFETY: dry-run mode
        self.gateways = {
            'stripe': StripeGateway(dry_run),
            'paypal': PayPalGateway(dry_run),
            'razorpay': RazorpayGateway(dry_run)
        }
    
    def setup_gateway(self, gateway_name: str, country: str, store_id: int) -> Dict[str, Any]:
        """Setup and verify payment gateway with dry-run support - PRODUCTION SAFETY"""
        gateway_name = gateway_name.lower()
        
        if self.dry_run:
            print(f"[DRY-RUN] Would setup payment gateway: {gateway_name} for country: {country}")
        
        # Verify gateway availability for country
        available = PAYMENT_COUNTRY_MAP.get(country, PAYMENT_COUNTRY_MAP['DEFAULT'])
        if gateway_name not in available:
            return {
                'success': False,
                'error': f'{gateway_name} not available in {country}'
            }
        
        gateway = self.gateways.get(gateway_name)
        if not gateway:
            return {
                'success': False,
                'error': f'Gateway {gateway_name} not implemented'
            }
        
        # Setup gateway
        setup_result = gateway.setup()
        if not setup_result['success']:
            return setup_result
        
        # Test with $1 transaction (skip in dry-run)
        if not self.dry_run:
            test_result = gateway.test_transaction(1.00, 'USD')
        else:
            print(f"[DRY-RUN] Would execute test transaction for {gateway_name}")
            test_result = {'success': True, 'transaction_id': 'dry-run-test-txn'}
        
        return {
            'success': test_result['success'],
            'gateway': gateway_name,
            'test_transaction_id': test_result.get('transaction_id'),
            'config': setup_result.get('config', {}),
            'error': test_result.get('error')
        }
    
    def get_gateway(self, gateway_name: str):
        """Get gateway instance"""
        return self.gateways.get(gateway_name.lower())


class StripeGateway:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run  # PRODUCTION SAFETY: dry-run mode
        self.api_key = CONFIG.STRIPE_SECRET_KEY
        self.publishable_key = CONFIG.STRIPE_PUBLISHABLE_KEY
        if not self.dry_run:
            stripe.api_key = self.api_key
    
    def setup(self) -> Dict[str, Any]:
        """Setup Stripe integration"""
        if not self.api_key:
            return {
                'success': False,
                'error': 'Stripe API key not configured'
            }
        
        try:
            # Verify API key
            stripe.Account.retrieve()
            
            return {
                'success': True,
                'config': {
                    'publishable_key': self.publishable_key,
                    'webhook_endpoint': '/webhooks/stripe'
                }
            }
        except stripe.error.AuthenticationError as e:
            return {
                'success': False,
                'error': f'Invalid Stripe API key: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Stripe setup failed: {str(e)}'
            }
    
    def test_transaction(self, amount: float, currency: str) -> Dict[str, Any]:
        """Create test payment intent with dry-run support - PRODUCTION SAFETY"""
        if not self.api_key:
            return {
                'success': False,
                'error': 'Stripe not configured'
            }
        
        # DRY RUN: Skip actual API call
        if self.dry_run:
            print(f"[DRY-RUN] Would create Stripe test payment: ${amount} {currency}")
            return {
                'success': True,
                'transaction_id': 'pi_dry_run_test',
                'status': 'dry_run'
            }
        
        try:
            # Create test payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Convert to cents
                currency=currency.lower(),
                payment_method_types=['card'],
                metadata={'test': 'true'}
            )
            
            return {
                'success': True,
                'transaction_id': intent.id,
                'status': intent.status
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Test transaction failed: {str(e)}'
            }
    
    def create_payment(self, amount: float, currency: str, 
                      metadata: Optional[Dict] = None) -> Dict[str, Any]:
        """Create payment intent"""
        try:
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),
                currency=currency.lower(),
                payment_method_types=['card'],
                metadata=metadata or {}
            )
            
            return {
                'success': True,
                'payment_id': intent.id,
                'client_secret': intent.client_secret,
                'status': intent.status
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def verify_payment(self, payment_intent_id: str) -> Dict[str, Any]:
        """Verify payment status"""
        try:
            intent = stripe.PaymentIntent.retrieve(payment_intent_id)
            return {
                'success': True,
                'status': intent.status,
                'amount': intent.amount / 100,
                'currency': intent.currency
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def setup_webhook(self, endpoint_url: str) -> Dict[str, Any]:
        """Setup Stripe webhook endpoint"""
        try:
            webhook = stripe.WebhookEndpoint.create(
                url=endpoint_url,
                enabled_events=[
                    'payment_intent.succeeded',
                    'payment_intent.payment_failed',
                    'charge.refunded'
                ]
            )
            
            return {
                'success': True,
                'webhook_id': webhook.id,
                'secret': webhook.secret
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class PayPalGateway:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run  # PRODUCTION SAFETY: dry-run mode
        self.client_id = CONFIG.PAYPAL_CLIENT_ID
        self.secret = CONFIG.PAYPAL_SECRET
        self.base_url = "https://api-m.sandbox.paypal.com"  # Use sandbox for testing
        self.access_token = None
    
    def _get_access_token(self) -> Optional[str]:
        """Get PayPal OAuth access token"""
        if not self.client_id or not self.secret:
            return None
        
        try:
            response = requests.post(
                f"{self.base_url}/v1/oauth2/token",
                auth=(self.client_id, self.secret),
                data={'grant_type': 'client_credentials'},
                timeout=30
            )
            
            if response.status_code == 200:
                self.access_token = response.json()['access_token']
                return self.access_token
        except Exception as e:
            print(f"PayPal auth error: {e}")
        
        return None
    
    def setup(self) -> Dict[str, Any]:
        """Setup PayPal integration"""
        if not self.client_id or not self.secret:
            return {
                'success': False,
                'error': 'PayPal credentials not configured'
            }
        
        token = self._get_access_token()
        if not token:
            return {
                'success': False,
                'error': 'Failed to authenticate with PayPal'
            }
        
        return {
            'success': True,
            'config': {
                'client_id': self.client_id,
                'mode': 'sandbox'
            }
        }
    
    def test_transaction(self, amount: float, currency: str) -> Dict[str, Any]:
        """Create test PayPal order with dry-run support - PRODUCTION SAFETY"""
        # DRY RUN: Skip actual API call
        if self.dry_run:
            print(f"[DRY-RUN] Would create PayPal test order: ${amount} {currency}")
            return {
                'success': True,
                'transaction_id': 'paypal_dry_run_test',
                'status': 'dry_run'
            }
        
        if not self.access_token:
            self._get_access_token()
        
        if not self.access_token:
            return {
                'success': False,
                'error': 'PayPal not configured'
            }
        
        try:
            order_data = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'amount': {
                        'currency_code': currency,
                        'value': str(amount)
                    }
                }]
            }
            
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                },
                json=order_data,
                timeout=30
            )
            
            if response.status_code == 201:
                order = response.json()
                return {
                    'success': True,
                    'transaction_id': order['id'],
                    'status': order['status']
                }
            else:
                return {
                    'success': False,
                    'error': f'PayPal order creation failed: {response.text}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_payment(self, amount: float, currency: str, 
                      return_url: str, cancel_url: str) -> Dict[str, Any]:
        """Create PayPal payment order"""
        if not self.access_token:
            self._get_access_token()
        
        try:
            order_data = {
                'intent': 'CAPTURE',
                'purchase_units': [{
                    'amount': {
                        'currency_code': currency,
                        'value': str(amount)
                    }
                }],
                'application_context': {
                    'return_url': return_url,
                    'cancel_url': cancel_url
                }
            }
            
            response = requests.post(
                f"{self.base_url}/v2/checkout/orders",
                headers={
                    'Authorization': f'Bearer {self.access_token}',
                    'Content-Type': 'application/json'
                },
                json=order_data,
                timeout=30
            )
            
            if response.status_code == 201:
                order = response.json()
                approve_link = next(
                    (link['href'] for link in order.get('links', []) 
                     if link['rel'] == 'approve'),
                    None
                )
                
                return {
                    'success': True,
                    'order_id': order['id'],
                    'approve_url': approve_link
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }


class RazorpayGateway:
    def __init__(self, dry_run: bool = False):
        self.dry_run = dry_run  # PRODUCTION SAFETY: dry-run mode
        self.key = CONFIG.RAZORPAY_KEY
        self.secret = CONFIG.RAZORPAY_SECRET
        self.base_url = "https://api.razorpay.com/v1"
    
    def setup(self) -> Dict[str, Any]:
        """Setup Razorpay integration"""
        if not self.key or not self.secret:
            return {
                'success': False,
                'error': 'Razorpay credentials not configured'
            }
        
        return {
            'success': True,
            'config': {
                'key_id': self.key
            }
        }
    
    def test_transaction(self, amount: float, currency: str) -> Dict[str, Any]:
        """Create test Razorpay order with dry-run support - PRODUCTION SAFETY"""
        # DRY RUN: Skip actual API call
        if self.dry_run:
            print(f"[DRY-RUN] Would create Razorpay test order: {amount} {currency}")
            return {
                'success': True,
                'transaction_id': 'razorpay_dry_run_test',
                'status': 'dry_run'
            }
        
        if not self.key or not self.secret:
            return {
                'success': False,
                'error': 'Razorpay not configured'
            }
        
        try:
            order_data = {
                'amount': int(amount * 100),  # Convert to paise
                'currency': currency,
                'notes': {'test': 'true'}
            }
            
            response = requests.post(
                f"{self.base_url}/orders",
                auth=(self.key, self.secret),
                json=order_data,
                timeout=30
            )
            
            if response.status_code == 200:
                order = response.json()
                return {
                    'success': True,
                    'transaction_id': order['id'],
                    'status': order['status']
                }
            else:
                return {
                    'success': False,
                    'error': f'Razorpay order failed: {response.text}'
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
    
    def create_payment(self, amount: float, currency: str) -> Dict[str, Any]:
        """Create Razorpay order"""
        try:
            order_data = {
                'amount': int(amount * 100),
                'currency': currency
            }
            
            response = requests.post(
                f"{self.base_url}/orders",
                auth=(self.key, self.secret),
                json=order_data,
                timeout=30
            )
            
            if response.status_code == 200:
                order = response.json()
                return {
                    'success': True,
                    'order_id': order['id'],
                    'amount': order['amount'],
                    'currency': order['currency']
                }
        except Exception as e:
            return {
                'success': False,
                'error': str(e)
            }
