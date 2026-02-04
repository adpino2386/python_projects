"""
OpenStreetMap (OSM) Service - FREE Alternative to Google Places API
Uses Nominatim for geocoding and Overpass API for business searches
No API key required!
"""
import requests
import time
from typing import List, Dict, Optional
from urllib.parse import quote


class OSMService:
    """Service for interacting with OpenStreetMap APIs (Nominatim + Overpass)"""
    
    def __init__(self):
        # Use a user agent to identify your application (required by Nominatim)
        self.headers = {
            'User-Agent': 'RadarLead/1.0 (Business Lead Finder)'
        }
        self.nominatim_url = "https://nominatim.openstreetmap.org"
        self.overpass_url = "https://overpass-api.de/api/interpreter"
        # Rate limiting: Nominatim allows 1 request per second
        self.last_request_time = 0
    
    def _rate_limit(self):
        """Respect Nominatim's rate limit (1 request per second)"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < 1.0:
            time.sleep(1.0 - time_since_last)
        self.last_request_time = time.time()
    
    def geocode(self, address: str) -> Optional[Dict]:
        """
        Geocode an address to get coordinates using Nominatim.
        
        Args:
            address: Address string (e.g., "Montreal, Quebec, Canada")
            
        Returns:
            Dictionary with lat, lng, and display_name or None
        """
        self._rate_limit()
        
        params = {
            'q': address,
            'format': 'json',
            'limit': 1
        }
        
        try:
            response = requests.get(f"{self.nominatim_url}/search", params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if data:
                result = data[0]
                return {
                    'lat': float(result['lat']),
                    'lng': float(result['lon']),
                    'display_name': result.get('display_name', address)
                }
        except Exception as e:
            print(f"Geocoding error: {e}")
        
        return None
    
    def search_businesses_nearby(self, lat: float, lng: float, business_type: str, radius: int = 5000) -> List[Dict]:
        """
        Search for businesses near a location using Overpass API.
        
        Args:
            lat: Latitude
            lng: Longitude
            business_type: Type of business (e.g., "plumber", "hotel", "restaurant")
            radius: Search radius in meters (default: 5km)
            
        Returns:
            List of business dictionaries
        """
        # Map common business types to OSM tags
        business_tags = self._get_osm_tags(business_type)
        
        businesses = []
        
        # Overpass QL query to find businesses in radius
        # This searches for nodes and ways with relevant tags
        query = f"""
        [out:json][timeout:25];
        (
          node["amenity"~"{business_tags['amenity']}"](around:{radius},{lat},{lng});
          way["amenity"~"{business_tags['amenity']}"](around:{radius},{lat},{lng});
          node["shop"~"{business_tags['shop']}"](around:{radius},{lat},{lng});
          way["shop"~"{business_tags['shop']}"](around:{radius},{lat},{lng});
        );
        out center meta;
        """
        
        try:
            response = requests.post(
                self.overpass_url,
                data={'data': query},
                headers=self.headers,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()
            
            if 'elements' in data:
                for element in data['elements']:
                    # Get coordinates
                    if element['type'] == 'node':
                        elem_lat = element.get('lat')
                        elem_lng = element.get('lon')
                    elif element['type'] == 'way' and 'center' in element:
                        elem_lat = element['center'].get('lat')
                        elem_lng = element['center'].get('lon')
                    else:
                        continue
                    
                    tags = element.get('tags', {})
                    
                    # Extract business information
                    business = {
                        'name': tags.get('name', 'Unnamed Business'),
                        'address': self._format_address(tags),
                        'phone': tags.get('phone') or tags.get('contact:phone', ''),
                        'website': tags.get('website') or tags.get('contact:website', ''),
                        'has_website': bool(tags.get('website') or tags.get('contact:website')),
                        'latitude': elem_lat,
                        'longitude': elem_lng,
                        'business_type': business_type,
                        'osm_id': element.get('id'),
                        'osm_type': element['type']
                    }
                    
                    businesses.append(business)
        
        except Exception as e:
            print(f"Overpass API error: {e}")
            raise
        
        return businesses
    
    def search_businesses_by_location(self, location: str, business_type: str) -> List[Dict]:
        """
        Search for businesses in a location using text search.
        
        Args:
            location: Location string (e.g., "Montreal, Quebec, Canada")
            business_type: Type of business
            
        Returns:
            List of business dictionaries
        """
        # First geocode the location
        geocode_result = self.geocode(location)
        
        if not geocode_result:
            return []
        
        # Then search nearby (using a reasonable radius for city searches)
        return self.search_businesses_nearby(
            geocode_result['lat'],
            geocode_result['lng'],
            business_type,
            radius=10000  # 10km for city searches
        )
    
    def _get_osm_tags(self, business_type: str) -> Dict[str, str]:
        """
        Map business types to OSM tags.
        OSM uses tags like amenity=restaurant, shop=plumber, etc.
        """
        business_type_lower = business_type.lower()
        
        # Common mappings
        mappings = {
            'plumber': {'amenity': '|', 'shop': 'plumber'},
            'hotel': {'amenity': 'hotel', 'shop': '|'},
            'restaurant': {'amenity': 'restaurant', 'shop': '|'},
            'restaurants': {'amenity': 'restaurant', 'shop': '|'},
            'cafe': {'amenity': 'cafe', 'shop': '|'},
            'coffee': {'amenity': 'cafe', 'shop': '|'},
            'bar': {'amenity': 'bar', 'shop': '|'},
            'pharmacy': {'amenity': 'pharmacy', 'shop': 'pharmacy'},
            'supermarket': {'amenity': '|', 'shop': 'supermarket'},
            'gas': {'amenity': 'fuel', 'shop': '|'},
            'gas station': {'amenity': 'fuel', 'shop': '|'},
        }
        
        # Try to find a match
        for key, tags in mappings.items():
            if key in business_type_lower:
                return tags
        
        # Default: search for any amenity or shop
        return {'amenity': '.*', 'shop': '.*'}
    
    def _format_address(self, tags: Dict) -> str:
        """Format address from OSM tags"""
        address_parts = []
        
        if tags.get('addr:housenumber') and tags.get('addr:street'):
            address_parts.append(f"{tags['addr:housenumber']} {tags['addr:street']}")
        elif tags.get('addr:street'):
            address_parts.append(tags['addr:street'])
        
        if tags.get('addr:city'):
            address_parts.append(tags['addr:city'])
        elif tags.get('addr:town'):
            address_parts.append(tags['addr:town'])
        
        if tags.get('addr:postcode'):
            address_parts.append(tags['addr:postcode'])
        
        if tags.get('addr:country'):
            address_parts.append(tags['addr:country'])
        
        return ', '.join(address_parts) if address_parts else tags.get('addr:full', '')
    
    def filter_businesses_without_website(self, businesses: List[Dict]) -> List[Dict]:
        """Filter businesses that don't have a website"""
        return [b for b in businesses if not b.get('has_website', False)]

