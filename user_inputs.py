import json
from typing import Dict, Any, Optional
from config import PAYMENT_COUNTRY_MAP, CURRENCY_MAP, TIMEZONE_MAP

class UserInputCollector:
    def __init__(self):
        self.inputs = {}
    
    def validate_niche(self, niche: str) -> bool:
        return len(niche.strip()) > 0 and len(niche) <= 100
    
    def validate_country(self, country: str) -> bool:
        valid_countries = list(CURRENCY_MAP.keys())
        return country.upper() in valid_countries
    
    def validate_brand_name(self, name: str) -> bool:
        if len(name) < 2 or len(name) > 50:
            return False
        return name.replace(' ', '').replace('-', '').isalnum()
    
    def validate_payment_gateway(self, gateway: str, country: str) -> bool:
        available = PAYMENT_COUNTRY_MAP.get(country.upper(), PAYMENT_COUNTRY_MAP['DEFAULT'])
        return gateway.lower() in available
    
    def validate_product_source(self, source: str) -> bool:
        valid_sources = ['cj', 'dsers', 'aliexpress', 'manual']
        return source.lower() in valid_sources
    
    def collect_inputs_interactive(self) -> Dict[str, Any]:
        """Interactive CLI collection - used for manual testing"""
        print("=== Auto Store Setup - Input Collection ===\n")
        
        # Niche
        while True:
            niche = input("Enter your store niche (e.g., fitness, beauty, tech): ").strip()
            if self.validate_niche(niche):
                self.inputs['niche'] = niche
                break
            print("Invalid niche. Please enter a valid niche name.")
        
        # Country
        while True:
            country = input("Enter target country code (US, CA, GB, AU, IN, SG, AE, EU): ").strip().upper()
            if self.validate_country(country):
                self.inputs['country'] = country
                self.inputs['currency'] = CURRENCY_MAP[country]
                self.inputs['timezone'] = TIMEZONE_MAP.get(country, "UTC")
                break
            print("Invalid country code.")
        
        # Brand name
        while True:
            brand = input("Enter your brand name: ").strip()
            if self.validate_brand_name(brand):
                self.inputs['brand_name'] = brand
                break
            print("Invalid brand name. Use 2-50 alphanumeric characters.")
        
        # Logo preference
        logo_pref = input("Auto-generate logo? (yes/no) [default: yes]: ").strip().lower()
        self.inputs['auto_logo'] = logo_pref != 'no'
        
        # Payment gateway
        available_gateways = PAYMENT_COUNTRY_MAP.get(self.inputs['country'], PAYMENT_COUNTRY_MAP['DEFAULT'])
        print(f"Available payment gateways for {self.inputs['country']}: {', '.join(available_gateways)}")
        
        while True:
            gateway = input(f"Choose payment gateway ({'/'.join(available_gateways)}): ").strip().lower()
            if self.validate_payment_gateway(gateway, self.inputs['country']):
                self.inputs['payment_gateway'] = gateway
                break
            print("Invalid gateway for this country.")
        
        # Product source
        while True:
            source = input("Product source (CJ/DSers/AliExpress/Manual): ").strip().lower()
            if self.validate_product_source(source):
                self.inputs['product_source'] = source
                break
            print("Invalid product source.")
        
        return self.inputs
    
    def collect_inputs_json(self, json_data: Dict[str, Any]) -> Dict[str, Any]:
        """Collection from JSON input - for automation"""
        required_fields = ['niche', 'country', 'brand_name', 'payment_gateway', 'product_source']
        
        for field in required_fields:
            if field not in json_data:
                raise ValueError(f"Missing required field: {field}")
        
        if not self.validate_niche(json_data['niche']):
            raise ValueError("Invalid niche")
        
        if not self.validate_country(json_data['country']):
            raise ValueError("Invalid country code")
        
        if not self.validate_brand_name(json_data['brand_name']):
            raise ValueError("Invalid brand name")
        
        country = json_data['country'].upper()
        
        if not self.validate_payment_gateway(json_data['payment_gateway'], country):
            raise ValueError(f"Invalid payment gateway for country {country}")
        
        if not self.validate_product_source(json_data['product_source']):
            raise ValueError("Invalid product source")
        
        self.inputs = {
            'niche': json_data['niche'].strip(),
            'country': country,
            'brand_name': json_data['brand_name'].strip(),
            'auto_logo': json_data.get('auto_logo', True),
            'payment_gateway': json_data['payment_gateway'].lower(),
            'product_source': json_data['product_source'].lower(),
            'currency': CURRENCY_MAP[country],
            'timezone': TIMEZONE_MAP.get(country, "UTC"),
            'color_scheme': json_data.get('color_scheme', 'modern')
        }
        
        return self.inputs
    
    def save_profile(self, filepath: str):
        """Save collected inputs to JSON file"""
        with open(filepath, 'w') as f:
            json.dump(self.inputs, f, indent=2)
    
    def load_profile(self, filepath: str) -> Dict[str, Any]:
        """Load inputs from JSON file"""
        with open(filepath, 'r') as f:
            data = json.load(f)
        return self.collect_inputs_json(data)

def create_store_profile(input_mode: str = 'json', json_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Main entry point for collecting user inputs
    
    Args:
        input_mode: 'interactive' or 'json'
        json_data: Dictionary containing user inputs (if mode is 'json')
    
    Returns:
        Dictionary with validated user inputs
    """
    collector = UserInputCollector()
    
    if input_mode == 'interactive':
        profile = collector.collect_inputs_interactive()
    elif input_mode == 'json' and json_data:
        profile = collector.collect_inputs_json(json_data)
    else:
        raise ValueError("Invalid input mode or missing JSON data")
    
    return profile
