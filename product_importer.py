import requests
from typing import Dict, Any, List, Optional
from config import CONFIG
import re
import time
from PIL import Image
import io

class ProductImporter:
    def __init__(self, wc_auth: tuple):
        self.wc_auth = wc_auth
        self.suppliers = {
            'cj': CJDropshippingAPI(),
            'aliexpress': AliExpressAPI(),
            'manual': ManualProductSource()
        }
    
    def import_products(self, source: str, niche: str, count: int = 10) -> List[Dict[str, Any]]:
        """Import products from supplier"""
        supplier = self.suppliers.get(source)
        if not supplier:
            raise ValueError(f"Unknown supplier: {source}")
        
        products = supplier.fetch_products(niche, count)
        return products
    
    def rewrite_title(self, original_title: str, niche: str) -> str:
        """Rewrite product title for SEO and clarity"""
        # Remove excessive special characters
        title = re.sub(r'[^a-zA-Z0-9\s\-]', '', original_title)
        
        # Capitalize properly
        title = ' '.join(word.capitalize() for word in title.split())
        
        # Add niche context if not present
        if niche.lower() not in title.lower():
            title = f"{title} - {niche.capitalize()}"
        
        # Limit length
        if len(title) > 60:
            title = title[:57] + '...'
        
        return title
    
    def rewrite_description(self, original_desc: str, title: str) -> str:
        """Rewrite product description"""
        if not original_desc:
            return f"High-quality {title.lower()}. Perfect for your needs. Fast shipping available."
        
        # Clean HTML tags
        desc = re.sub(r'<[^>]+>', '', original_desc)
        
        # Remove excessive whitespace
        desc = ' '.join(desc.split())
        
        # Add standard features
        features = [
            "✓ Premium Quality",
            "✓ Fast Shipping",
            "✓ 30-Day Returns",
            "✓ Secure Checkout"
        ]
        
        enhanced_desc = f"{desc}\n\n<strong>Why Choose Us?</strong>\n" + "\n".join(features)
        
        return enhanced_desc
    
    def calculate_pricing(self, cost_price: float, multiplier: float = CONFIG.PRICE_MULTIPLIER) -> Dict[str, float]:
        """Calculate selling price with margin"""
        selling_price = cost_price * multiplier
        margin_percent = ((selling_price - cost_price) / selling_price) * 100
        
        # Ensure minimum margin
        if margin_percent < CONFIG.MIN_MARGIN_PERCENT:
            multiplier = 1 / (1 - CONFIG.MIN_MARGIN_PERCENT / 100)
            selling_price = cost_price * multiplier
            margin_percent = CONFIG.MIN_MARGIN_PERCENT
        
        # Round to 2 decimals
        selling_price = round(selling_price, 2)
        
        return {
            'cost_price': cost_price,
            'selling_price': selling_price,
            'margin_percent': round(margin_percent, 2),
            'profit': round(selling_price - cost_price, 2)
        }
    
    def compress_image(self, image_url: str, output_path: str, quality: int = 85) -> str:
        """Download and compress product image"""
        try:
            response = requests.get(image_url, timeout=30)
            if response.status_code == 200:
                img = Image.open(io.BytesIO(response.content))
                
                # Convert to RGB if necessary
                if img.mode in ('RGBA', 'LA', 'P'):
                    img = img.convert('RGB')
                
                # Resize if too large
                max_size = (1200, 1200)
                img.thumbnail(max_size, Image.Resampling.LANCZOS)
                
                # Save compressed
                img.save(output_path, 'JPEG', quality=quality, optimize=True)
                return output_path
        except Exception as e:
            print(f"Image compression failed: {e}")
        
        return image_url
    
    def process_product(self, raw_product: Dict[str, Any], niche: str) -> Dict[str, Any]:
        """Process and enhance product data"""
        # Rewrite content
        new_title = self.rewrite_title(raw_product['title'], niche)
        new_desc = self.rewrite_description(raw_product.get('description', ''), new_title)
        
        # Calculate pricing
        pricing = self.calculate_pricing(raw_product['cost_price'])
        
        # Process images
        processed_images = []
        for idx, img_url in enumerate(raw_product.get('images', [])[:5]):
            # In production, compress and upload
            processed_images.append(img_url)
        
        processed = {
            'supplier_id': raw_product.get('id'),
            'title': new_title,
            'description': new_desc,
            'cost_price': pricing['cost_price'],
            'selling_price': pricing['selling_price'],
            'margin_percent': pricing['margin_percent'],
            'image_urls': processed_images,
            'variants': raw_product.get('variants', []),
            'inventory_count': raw_product.get('inventory', 100),
            'sku': raw_product.get('sku', f"SKU-{raw_product.get('id', 'AUTO')}")
        }
        
        return processed
    
    def upload_to_woocommerce(self, wc_api_base: str, product: Dict[str, Any]) -> Optional[int]:
        """Upload product to WooCommerce"""
        product_data = {
            'name': product['title'],
            'type': 'simple',
            'regular_price': str(product['selling_price']),
            'description': product['description'],
            'short_description': product['description'][:160],
            'sku': product['sku'],
            'manage_stock': True,
            'stock_quantity': product['inventory_count'],
            'images': [{'src': url} for url in product['image_urls']],
            'status': 'publish'
        }
        
        # Add variants if present
        if product.get('variants'):
            product_data['type'] = 'variable'
            product_data['attributes'] = self._format_variants(product['variants'])
        
        try:
            response = requests.post(
                f"{wc_api_base}/products",
                auth=self.wc_auth,
                json=product_data,
                timeout=30
            )
            
            if response.status_code == 201:
                result = response.json()
                return result.get('id')
            else:
                print(f"Product upload failed: {response.text}")
        except Exception as e:
            print(f"Product upload error: {e}")
        
        return None
    
    def _format_variants(self, variants: List[Dict]) -> List[Dict]:
        """Format variants for WooCommerce"""
        attributes = []
        
        # Group by attribute type (size, color, etc.)
        variant_types = {}
        for variant in variants:
            for key, value in variant.items():
                if key not in variant_types:
                    variant_types[key] = []
                if value not in variant_types[key]:
                    variant_types[key].append(value)
        
        for attr_name, options in variant_types.items():
            attributes.append({
                'name': attr_name.capitalize(),
                'visible': True,
                'variation': True,
                'options': options
            })
        
        return attributes
    
    def bulk_import(self, source: str, niche: str, wc_api_base: str, 
                   count: int = 10) -> Dict[str, Any]:
        """Bulk import and upload products"""
        results = {
            'imported': 0,
            'failed': 0,
            'product_ids': [],
            'errors': []
        }
        
        # Fetch products
        raw_products = self.import_products(source, niche, count)
        
        for raw_product in raw_products:
            try:
                # Process product
                processed = self.process_product(raw_product, niche)
                
                # Upload to WooCommerce
                product_id = self.upload_to_woocommerce(wc_api_base, processed)
                
                if product_id:
                    results['imported'] += 1
                    results['product_ids'].append(product_id)
                else:
                    results['failed'] += 1
                    results['errors'].append(f"Failed to upload: {processed['title']}")
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                results['failed'] += 1
                results['errors'].append(str(e))
        
        return results


class CJDropshippingAPI:
    def __init__(self):
        self.api_key = CONFIG.CJDROPSHIPPING_API_KEY
        self.base_url = "https://developers.cjdropshipping.com/api2.0/v1"
    
    def fetch_products(self, niche: str, count: int) -> List[Dict[str, Any]]:
        """Fetch products from CJ Dropshipping"""
        if not self.api_key:
            return self._mock_products(niche, count)
        
        try:
            response = requests.get(
                f"{self.base_url}/product/list",
                headers={"CJ-Access-Token": self.api_key},
                params={"categoryId": niche, "pageSize": count},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_cj_products(data.get('data', []))
        except Exception as e:
            print(f"CJ API error: {e}")
        
        return self._mock_products(niche, count)
    
    def _parse_cj_products(self, products: List[Dict]) -> List[Dict[str, Any]]:
        """Parse CJ product data"""
        parsed = []
        for p in products:
            parsed.append({
                'id': p.get('pid'),
                'title': p.get('productNameEn'),
                'description': p.get('description'),
                'cost_price': float(p.get('sellPrice', 10.0)),
                'images': [p.get('productImage')] if p.get('productImage') else [],
                'variants': p.get('variants', []),
                'inventory': p.get('stock', 100),
                'sku': p.get('productSku')
            })
        return parsed
    
    def _mock_products(self, niche: str, count: int) -> List[Dict[str, Any]]:
        """Generate mock products for testing"""
        products = []
        for i in range(count):
            products.append({
                'id': f"MOCK-{i+1}",
                'title': f"{niche.capitalize()} Product {i+1}",
                'description': f"High-quality {niche} product with excellent features.",
                'cost_price': round(10.0 + (i * 2.5), 2),
                'images': [f"https://via.placeholder.com/600?text=Product+{i+1}"],
                'variants': [],
                'inventory': 100,
                'sku': f"SKU-{niche.upper()}-{i+1:03d}"
            })
        return products


class AliExpressAPI:
    def fetch_products(self, niche: str, count: int) -> List[Dict[str, Any]]:
        """Mock AliExpress API - requires actual API credentials"""
        return CJDropshippingAPI()._mock_products(niche, count)


class ManualProductSource:
    def fetch_products(self, niche: str, count: int) -> List[Dict[str, Any]]:
        """Manual product entry"""
        return []
