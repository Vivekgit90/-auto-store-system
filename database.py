import sqlite3
from datetime import datetime
from typing import Optional, Dict, Any, Tuple
import json
import hashlib

class Database:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.init_db()
    
    def get_connection(self):
        return sqlite3.connect(self.db_path)
    
    def _generate_store_hash(self, store_data: Dict[str, Any]) -> str:
        """Generate deterministic hash for idempotency - PRODUCTION SAFETY"""
        key = f"{store_data['brand_name']}:{store_data['country']}:{store_data['niche']}"
        return hashlib.sha256(key.encode()).hexdigest()
    
    def _generate_product_hash(self, store_id: int, product: Dict[str, Any]) -> str:
        """Generate deterministic hash for product idempotency - PRODUCTION SAFETY"""
        supplier_id = product.get('supplier_id', '')
        title = product.get('title', '')
        key = f"{store_id}:{supplier_id}:{title}"
        return hashlib.sha256(key.encode()).hexdigest()
    
    def init_db(self):
        conn = self.get_connection()
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS stores (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_name TEXT NOT NULL,
                niche TEXT NOT NULL,
                country TEXT NOT NULL,
                brand_name TEXT NOT NULL,
                domain TEXT,
                currency TEXT NOT NULL,
                timezone TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                idempotency_hash TEXT UNIQUE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS brand_assets (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                logo_url TEXT,
                color_palette TEXT,
                tagline TEXT,
                brand_voice TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                supplier_id TEXT,
                title TEXT NOT NULL,
                description TEXT,
                cost_price REAL NOT NULL,
                selling_price REAL NOT NULL,
                margin_percent REAL,
                image_urls TEXT,
                variants TEXT,
                inventory_count INTEGER DEFAULT 0,
                status TEXT DEFAULT 'active',
                idempotency_hash TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id),
                UNIQUE(store_id, idempotency_hash)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                order_id TEXT UNIQUE NOT NULL,
                customer_email TEXT,
                total_amount REAL NOT NULL,
                payment_status TEXT DEFAULT 'pending',
                fulfillment_status TEXT DEFAULT 'unfulfilled',
                supplier_order_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS abandoned_carts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                cart_token TEXT UNIQUE NOT NULL,
                customer_email TEXT,
                items TEXT,
                total_value REAL,
                recovery_sent BOOLEAN DEFAULT 0,
                recovery_sent_at TIMESTAMP,
                recovered BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS automation_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER,
                job_type TEXT NOT NULL,
                status TEXT NOT NULL,
                message TEXT,
                error_details TEXT,
                execution_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS payment_configs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                gateway TEXT NOT NULL,
                config_data TEXT NOT NULL,
                is_active BOOLEAN DEFAULT 1,
                test_transaction_id TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS webhooks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                store_id INTEGER NOT NULL,
                event_type TEXT NOT NULL,
                payload TEXT NOT NULL,
                processed BOOLEAN DEFAULT 0,
                retry_count INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                processed_at TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        ''')
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS execution_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                execution_id TEXT UNIQUE NOT NULL,
                store_id INTEGER,
                env TEXT NOT NULL,
                dry_run BOOLEAN NOT NULL,
                status TEXT NOT NULL,
                steps_completed TEXT,
                steps_failed TEXT,
                errors TEXT,
                execution_time REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (store_id) REFERENCES stores(id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def create_store(self, store_data: Dict[str, Any]) -> Tuple[int, bool]:
        """
        Create store with idempotency protection - PRODUCTION SAFETY
        Returns: (store_id, was_created)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Generate idempotency hash
        idempotency_hash = self._generate_store_hash(store_data)
        
        # Check if store already exists
        cursor.execute(
            'SELECT id FROM stores WHERE idempotency_hash = ?',
            (idempotency_hash,)
        )
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return (existing[0], False)  # Return existing store, not created
        
        # Create new store
        cursor.execute('''
            INSERT INTO stores (store_name, niche, country, brand_name, currency, timezone, idempotency_hash)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            store_data['store_name'],
            store_data['niche'],
            store_data['country'],
            store_data['brand_name'],
            store_data['currency'],
            store_data['timezone'],
            idempotency_hash
        ))
        store_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return (store_id, True)  # Return new store, was created
    
    def save_brand_assets(self, store_id: int, assets: Dict[str, Any]):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO brand_assets (store_id, logo_url, color_palette, tagline, brand_voice)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            store_id,
            assets.get('logo_url'),
            json.dumps(assets.get('color_palette', [])),
            assets.get('tagline'),
            assets.get('brand_voice')
        ))
        conn.commit()
        conn.close()
    
    def create_product(self, store_id: int, product: Dict[str, Any]) -> Tuple[int, bool]:
        """
        Create product with idempotency protection - PRODUCTION SAFETY
        Returns: (product_id, was_created)
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        
        # Generate idempotency hash
        idempotency_hash = self._generate_product_hash(store_id, product)
        
        # Check if product already exists
        cursor.execute(
            'SELECT id FROM products WHERE store_id = ? AND idempotency_hash = ?',
            (store_id, idempotency_hash)
        )
        existing = cursor.fetchone()
        
        if existing:
            conn.close()
            return (existing[0], False)  # Return existing product, not created
        
        # Create new product
        cursor.execute('''
            INSERT INTO products (
                store_id, supplier_id, title, description, cost_price, 
                selling_price, margin_percent, image_urls, variants, inventory_count, idempotency_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            store_id,
            product.get('supplier_id'),
            product['title'],
            product.get('description'),
            product['cost_price'],
            product['selling_price'],
            product.get('margin_percent'),
            json.dumps(product.get('image_urls', [])),
            json.dumps(product.get('variants', [])),
            product.get('inventory_count', 0),
            idempotency_hash
        ))
        product_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return (product_id, True)  # Return new product, was created
    
    def log_automation(self, store_id: Optional[int], job_type: str, status: str, 
                       message: str, error: Optional[str] = None, exec_time: Optional[float] = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO automation_logs (store_id, job_type, status, message, error_details, execution_time)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (store_id, job_type, status, message, error, exec_time))
        conn.commit()
        conn.close()
    
    def save_payment_config(self, store_id: int, gateway: str, config: Dict[str, Any], test_txn_id: Optional[str] = None):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO payment_configs (store_id, gateway, config_data, test_transaction_id)
            VALUES (?, ?, ?, ?)
        ''', (store_id, gateway, json.dumps(config), test_txn_id))
        conn.commit()
        conn.close()
    
    def create_order(self, store_id: int, order_data: Dict[str, Any]) -> int:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO orders (store_id, order_id, customer_email, total_amount, payment_status)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            store_id,
            order_data['order_id'],
            order_data.get('customer_email'),
            order_data['total_amount'],
            order_data.get('payment_status', 'pending')
        ))
        order_pk = cursor.lastrowid
        conn.commit()
        conn.close()
        return order_pk
    
    def save_abandoned_cart(self, store_id: int, cart_data: Dict[str, Any]):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO abandoned_carts 
            (store_id, cart_token, customer_email, items, total_value)
            VALUES (?, ?, ?, ?, ?)
        ''', (
            store_id,
            cart_data['cart_token'],
            cart_data.get('customer_email'),
            json.dumps(cart_data.get('items', [])),
            cart_data.get('total_value', 0)
        ))
        conn.commit()
        conn.close()
    
    def get_pending_webhooks(self, limit: int = 100):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, store_id, event_type, payload, retry_count
            FROM webhooks
            WHERE processed = 0 AND retry_count < 3
            ORDER BY created_at ASC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()
        return rows
    
    def mark_webhook_processed(self, webhook_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE webhooks
            SET processed = 1, processed_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (webhook_id,))
        conn.commit()
        conn.close()
    
    def increment_webhook_retry(self, webhook_id: int):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE webhooks
            SET retry_count = retry_count + 1
            WHERE id = ?
        ''', (webhook_id,))
        conn.commit()
        conn.close()
    
    def get_store(self, store_id: int) -> Optional[Dict[str, Any]]:
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM stores WHERE id = ?', (store_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            columns = [desc[0] for desc in cursor.description]
            return dict(zip(columns, row))
        return None
    
    def update_store_status(self, store_id: int, status: str):
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE stores SET status = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (status, store_id))
        conn.commit()
        conn.close()
    
    def save_execution_report(self, execution_id: str, report_data: Dict[str, Any]):
        """Save execution report for audit trail - PRODUCTION SAFETY"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO execution_reports 
            (execution_id, store_id, env, dry_run, status, steps_completed, steps_failed, errors, execution_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            execution_id,
            report_data.get('store_id'),
            report_data.get('env', 'dev'),
            report_data.get('dry_run', False),
            report_data.get('status', 'unknown'),
            json.dumps(report_data.get('steps_completed', [])),
            json.dumps(report_data.get('steps_failed', [])),
            json.dumps(report_data.get('errors', [])),
            report_data.get('execution_time', 0.0)
        ))
        conn.commit()
        conn.close()
    
    def get_execution_report(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve execution report - PRODUCTION SAFETY"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM execution_reports WHERE execution_id = ?', (execution_id,))
        row = cursor.fetchone()
        conn.close()
        if row:
            columns = ['id', 'execution_id', 'store_id', 'env', 'dry_run', 'status', 
                      'steps_completed', 'steps_failed', 'errors', 'execution_time', 'created_at']
            return dict(zip(columns, row))
        return None
