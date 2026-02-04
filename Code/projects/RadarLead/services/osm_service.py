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
        
        # Add more specific parameters to improve geocoding accuracy
        params = {
            'q': address,
            'format': 'json',
            'limit': 1,
            'addressdetails': 1,  # Get detailed address components
            'extratags': 1  # Get extra tags for better matching
        }
        
        try:
            response = requests.get(f"{self.nominatim_url}/search", params=params, headers=self.headers)
            response.raise_for_status()
            data = response.json()
            
            if data:
                result = data[0]
                # Check if the result actually matches the requested city
                address_parts = result.get('address', {})
                city_match = False
                
                # Extract city name from address components
                city_name = (address_parts.get('city') or 
                           address_parts.get('town') or 
                           address_parts.get('municipality') or 
                           address_parts.get('village', '')).lower()
                
                # Check if the requested address contains the city name from result
                address_lower = address.lower()
                if city_name and city_name in address_lower:
                    city_match = True
                
                return {
                    'lat': float(result['lat']),
                    'lng': float(result['lon']),
                    'display_name': result.get('display_name', address),
                    'city': city_name,
                    'matched': city_match
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
        
        # Build Overpass QL query based on what tags we have
        query_parts = []
        
        # Add amenity searches if we have specific amenity tags
        # Use exact match (=) instead of regex (~) for better precision
        if business_tags['amenity'] and business_tags['amenity'] != '|':
            amenity_value = business_tags['amenity'].replace('^', '').replace('$', '')
            query_parts.append(f'node["amenity"="{amenity_value}"](around:{radius},{lat},{lng});')
            query_parts.append(f'way["amenity"="{amenity_value}"](around:{radius},{lat},{lng});')
        
        # Add shop searches if we have specific shop tags
        if business_tags['shop'] and business_tags['shop'] != '|':
            shop_value = business_tags['shop'].replace('^', '').replace('$', '')
            query_parts.append(f'node["shop"="{shop_value}"](around:{radius},{lat},{lng});')
            query_parts.append(f'way["shop"="{shop_value}"](around:{radius},{lat},{lng});')
        
        # Add tourism searches (for hotels, hostels, etc.)
        if business_tags.get('tourism') and business_tags['tourism'] != '|':
            tourism_value = business_tags['tourism'].replace('^', '').replace('$', '')
            query_parts.append(f'node["tourism"="{tourism_value}"](around:{radius},{lat},{lng});')
            query_parts.append(f'way["tourism"="{tourism_value}"](around:{radius},{lat},{lng});')
        
        # If no specific tags, don't search (avoid returning everything)
        if not query_parts:
            return []
        
        # Overpass QL query to find businesses in radius
        query = f"""
        [out:json][timeout:25];
        (
          {' '.join(query_parts)}
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
                    # Determine actual business type from OSM tags (check tourism, amenity, shop)
                    actual_business_type = tags.get('tourism') or tags.get('amenity') or tags.get('shop') or business_type
                    
                    business = {
                        'name': tags.get('name', 'Unnamed Business'),
                        'address': self._format_address(tags),
                        'phone': tags.get('phone') or tags.get('contact:phone', ''),
                        'website': tags.get('website') or tags.get('contact:website', ''),
                        'has_website': bool(tags.get('website') or tags.get('contact:website')),
                        'latitude': elem_lat,
                        'longitude': elem_lng,
                        'business_type': actual_business_type,  # Use actual OSM tag, not search term
                        'search_term': business_type,  # Keep original search term for reference
                        'osm_id': element.get('id'),
                        'osm_type': element['type']
                    }
                    
                    businesses.append(business)
        
        except Exception as e:
            print(f"Overpass API error: {e}")
            raise
        
        return businesses
    
    def search_businesses_by_location(self, location: str, business_type: str, radius: int = 5000) -> List[Dict]:
        """
        Search for businesses in a location using text search.
        
        Args:
            location: Location string (e.g., "Montreal, Quebec, Canada")
            business_type: Type of business
            radius: Search radius in meters (default: 5km, reduced from 10km for better accuracy)
            
        Returns:
            List of business dictionaries
        """
        # First geocode the location
        geocode_result = self.geocode(location)
        
        if not geocode_result:
            return []
        
        # Warn if geocoding might not have matched the exact city
        if not geocode_result.get('matched', True):
            print(f"⚠️ Geocoding warning: Result may not match exact city in '{location}'")
            print(f"   Found: {geocode_result.get('display_name', 'Unknown')}")
        
        # Then search nearby (using a smaller radius for better accuracy)
        return self.search_businesses_nearby(
            geocode_result['lat'],
            geocode_result['lng'],
            business_type,
            radius=radius
        )
    
    def _get_osm_tags(self, business_type: str) -> Dict[str, str]:
        """
        Map business types to OSM tags.
        OSM uses tags like amenity=restaurant, shop=plumber, tourism=hotel, etc.
        Returns dict with 'amenity', 'shop', and 'tourism' keys. Use '|' to skip that category.
        """
        business_type_lower = business_type.lower().strip()
        
        # Common mappings - be specific to avoid false matches
        # NOTE: Hotels in OSM are typically tagged as tourism=hotel, not amenity=hotel
        mappings = {
            # Hotels - use tourism=hotel (most common in OSM)
            'hotel': {'amenity': '|', 'shop': '|', 'tourism': 'hotel'},
            'hotels': {'amenity': '|', 'shop': '|', 'tourism': 'hotel'},
            
            # Plumbers
            'plumber': {'amenity': '|', 'shop': 'plumber', 'tourism': '|'},
            'plumbers': {'amenity': '|', 'shop': 'plumber', 'tourism': '|'},
            
            # Restaurants
            'restaurant': {'amenity': 'restaurant', 'shop': '|', 'tourism': '|'},
            'restaurants': {'amenity': 'restaurant', 'shop': '|', 'tourism': '|'},
            
            # Cafes
            'cafe': {'amenity': 'cafe', 'shop': '|', 'tourism': '|'},
            'cafes': {'amenity': 'cafe', 'shop': '|', 'tourism': '|'},
            'coffee': {'amenity': 'cafe', 'shop': '|', 'tourism': '|'},
            
            # Bars
            'bar': {'amenity': 'bar', 'shop': '|', 'tourism': '|'},
            'bars': {'amenity': 'bar', 'shop': '|', 'tourism': '|'},
            
            # Pharmacies
            'pharmacy': {'amenity': 'pharmacy', 'shop': 'pharmacy', 'tourism': '|'},
            'pharmacies': {'amenity': 'pharmacy', 'shop': 'pharmacy', 'tourism': '|'},
            
            # Supermarkets
            'supermarket': {'amenity': '|', 'shop': 'supermarket', 'tourism': '|'},
            'supermarkets': {'amenity': '|', 'shop': 'supermarket', 'tourism': '|'},
            
            # Gas stations
            'gas': {'amenity': 'fuel', 'shop': '|', 'tourism': '|'},
            'gas station': {'amenity': 'fuel', 'shop': '|', 'tourism': '|'},
            'gas stations': {'amenity': 'fuel', 'shop': '|', 'tourism': '|'},
            'fuel': {'amenity': 'fuel', 'shop': '|', 'tourism': '|'},
            
            # Car dealerships
            'car dealer': {'amenity': '|', 'shop': 'car', 'tourism': '|'},
            'car dealership': {'amenity': '|', 'shop': 'car', 'tourism': '|'},
            'car': {'amenity': '|', 'shop': 'car', 'tourism': '|'},
            
            # Grocery stores
            'grocery': {'amenity': '|', 'shop': 'supermarket', 'tourism': '|'},
            'grocery store': {'amenity': '|', 'shop': 'supermarket', 'tourism': '|'},
        }
        
        # Try to find an exact match first
        if business_type_lower in mappings:
            return mappings[business_type_lower]
        
        # Try to find a partial match
        for key, tags in mappings.items():
            if key in business_type_lower or business_type_lower in key:
                return tags
        
        # If no match found, return empty (don't search for everything)
        # This prevents returning all businesses when the type is unknown
        return {'amenity': '|', 'shop': '|', 'tourism': '|'}
    
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

