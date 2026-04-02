import random
import requests
import hashlib
from typing import Dict, List, Any, Optional
from config import CONFIG, COLOR_PALETTES
import re

class BrandAssetGenerator:
    def __init__(self):
        self.openai_api_key = CONFIG.OPENAI_API_KEY
        self.stability_api_key = CONFIG.STABILITY_API_KEY
    
    def generate_brand_variations(self, brand_name: str, niche: str) -> List[str]:
        """Generate brand name variations using pattern rules"""
        variations = [brand_name]
        clean_name = brand_name.replace(' ', '')
        
        # Suffix patterns
        suffixes = ['Shop', 'Store', 'Hub', 'Mart', 'Express', 'Direct', 'Pro']
        for suffix in suffixes[:3]:
            variations.append(f"{brand_name} {suffix}")
            variations.append(f"{clean_name}{suffix}")
        
        # Prefix patterns
        if niche:
            variations.append(f"{niche.capitalize()} {brand_name}")
            variations.append(f"The {brand_name}")
        
        # Domain-friendly
        variations.append(clean_name.lower())
        variations.append(f"get{clean_name.lower()}")
        variations.append(f"my{clean_name.lower()}")
        
        return list(set(variations))[:10]
    
    def generate_logo_simple(self, brand_name: str, color_palette: List[str], output_path: str) -> str:
        """Generate simple SVG logo without external APIs"""
        initials = ''.join([word[0].upper() for word in brand_name.split()[:2]])
        if len(initials) == 0:
            initials = brand_name[:2].upper()
        
        primary_color = color_palette[0] if color_palette else "#2C3E50"
        secondary_color = color_palette[1] if len(color_palette) > 1 else "#ECF0F1"
        
        svg_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="200" fill="{primary_color}" rx="20"/>
  <text x="100" y="120" font-family="Arial, sans-serif" font-size="72" font-weight="bold" 
        fill="{secondary_color}" text-anchor="middle">{initials}</text>
</svg>'''
        
        with open(output_path, 'w') as f:
            f.write(svg_content)
        
        return output_path
    
    def generate_logo_via_api(self, brand_name: str, niche: str, color_scheme: str) -> Optional[str]:
        """Generate logo using free AI API (with fallback)"""
        if not self.stability_api_key:
            return None
        
        prompt = f"minimalist logo design for '{brand_name}', {niche} brand, {color_scheme} color scheme, simple icon, professional, vector style"
        
        try:
            response = requests.post(
                "https://api.stability.ai/v1/generation/stable-diffusion-xl-1024-v1-0/text-to-image",
                headers={
                    "Authorization": f"Bearer {self.stability_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "text_prompts": [{"text": prompt, "weight": 1}],
                    "cfg_scale": 7,
                    "height": 512,
                    "width": 512,
                    "samples": 1,
                    "steps": 30
                },
                timeout=60
            )
            
            if response.status_code == 200:
                data = response.json()
                if 'artifacts' in data and len(data['artifacts']) > 0:
                    import base64
                    image_data = base64.b64decode(data['artifacts'][0]['base64'])
                    filename = f"logo_{hashlib.md5(brand_name.encode()).hexdigest()}.png"
                    with open(filename, 'wb') as f:
                        f.write(image_data)
                    return filename
        except Exception as e:
            print(f"Logo API generation failed: {e}")
        
        return None
    
    def select_color_palette(self, niche: str, preference: str = 'modern') -> List[str]:
        """Select appropriate color palette based on niche"""
        niche_lower = niche.lower()
        
        # Niche-based palette selection
        if any(word in niche_lower for word in ['eco', 'nature', 'organic', 'green', 'sustainable']):
            return COLOR_PALETTES['nature']
        elif any(word in niche_lower for word in ['tech', 'software', 'digital', 'ai', 'crypto']):
            return COLOR_PALETTES['tech']
        elif any(word in niche_lower for word in ['luxury', 'premium', 'fashion', 'jewelry']):
            return COLOR_PALETTES['luxury']
        elif any(word in niche_lower for word in ['kids', 'baby', 'toy', 'children']):
            return COLOR_PALETTES['vibrant']
        elif any(word in niche_lower for word in ['minimal', 'simple', 'clean']):
            return COLOR_PALETTES['minimal']
        else:
            return COLOR_PALETTES.get(preference, COLOR_PALETTES['modern'])
    
    def generate_tagline(self, brand_name: str, niche: str) -> str:
        """Generate tagline using template patterns"""
        templates = [
            f"Your Trusted {niche.capitalize()} Partner",
            f"Elevate Your {niche.capitalize()} Experience",
            f"Quality {niche.capitalize()} Products, Delivered",
            f"Where {niche.capitalize()} Meets Excellence",
            f"Premium {niche.capitalize()} Solutions",
            f"Redefining {niche.capitalize()}",
            f"{niche.capitalize()} Made Simple",
            f"The Future of {niche.capitalize()}",
            f"Your {niche.capitalize()} Destination",
            f"Exceptional {niche.capitalize()}, Every Time"
        ]
        
        # Select based on hash for consistency
        index = hash(brand_name + niche) % len(templates)
        return templates[index]
    
    def generate_tagline_via_api(self, brand_name: str, niche: str) -> Optional[str]:
        """Generate creative tagline using OpenAI API"""
        if not self.openai_api_key:
            return None
        
        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.openai_api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "gpt-3.5-turbo",
                    "messages": [
                        {
                            "role": "system",
                            "content": "You are a brand strategist. Generate a short, catchy tagline (max 6 words)."
                        },
                        {
                            "role": "user",
                            "content": f"Create a tagline for '{brand_name}', a {niche} brand."
                        }
                    ],
                    "max_tokens": 30,
                    "temperature": 0.8
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                tagline = data['choices'][0]['message']['content'].strip()
                # Remove quotes if present
                tagline = tagline.strip('"\'')
                return tagline
        except Exception as e:
            print(f"Tagline API generation failed: {e}")
        
        return None
    
    def generate_brand_voice(self, niche: str, target_country: str) -> str:
        """Generate brand voice guidelines"""
        tone_map = {
            'tech': "innovative, professional, forward-thinking",
            'fashion': "stylish, trendy, aspirational",
            'fitness': "motivational, energetic, empowering",
            'beauty': "elegant, confident, transformative",
            'home': "warm, comfortable, inviting",
            'food': "appetizing, authentic, passionate",
            'kids': "playful, safe, caring",
            'luxury': "sophisticated, exclusive, refined"
        }
        
        niche_lower = niche.lower()
        tone = "friendly, helpful, trustworthy"
        
        for key, value in tone_map.items():
            if key in niche_lower:
                tone = value
                break
        
        return f"Tone: {tone}. Voice: Clear, concise, customer-focused. Language: Conversational yet professional."
    
    def generate_all_assets(self, brand_name: str, niche: str, 
                          color_preference: str = 'modern',
                          auto_logo: bool = True) -> Dict[str, Any]:
        """Generate complete brand asset package"""
        assets = {}
        
        # Brand variations
        assets['brand_variations'] = self.generate_brand_variations(brand_name, niche)
        
        # Color palette
        assets['color_palette'] = self.select_color_palette(niche, color_preference)
        
        # Logo
        if auto_logo:
            logo_path = f"./brand_assets/logo_{brand_name.replace(' ', '_').lower()}.svg"
            import os
            os.makedirs("./brand_assets", exist_ok=True)
            
            # Try API first, fallback to simple generation
            api_logo = self.generate_logo_via_api(brand_name, niche, color_preference)
            if api_logo:
                assets['logo_url'] = api_logo
            else:
                assets['logo_url'] = self.generate_logo_simple(brand_name, assets['color_palette'], logo_path)
        else:
            assets['logo_url'] = None
        
        # Tagline
        api_tagline = self.generate_tagline_via_api(brand_name, niche)
        if api_tagline:
            assets['tagline'] = api_tagline
        else:
            assets['tagline'] = self.generate_tagline(brand_name, niche)
        
        # Brand voice
        assets['brand_voice'] = self.generate_brand_voice(niche, 'US')
        
        return assets
