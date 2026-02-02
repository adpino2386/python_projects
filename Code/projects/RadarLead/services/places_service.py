"""
Google Places API Service
A more reliable alternative to web scraping for finding businesses.
"""
import os
import requests
from typing import List, Dict, Optional
import time


class PlacesService:
    """Service for interacting with Google Places API"""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv('GOOGLE_PLACES_API_KEY')
        if not self.api_key:
            raise ValueError("Google Places API key is required. Set GOOGLE_PLACES_API_KEY environment variable.")
        
        self.base_url = "https://maps.googleapis.com/maps/api/place"
    
    def search_by_text(self, query: str, location: str = None, max_results: int = 60) -> List[Dict]:
        """
        Search for places using text query.
        
        Args:
            query: Business type (e.g., "Plumbers in Montreal")
            location: Optional location bias (e.g., "Montreal, Quebec, Canada")
            max_results: Maximum number of results to return
            
        Returns:
            List of business dictionaries
        """
        businesses = []
        next_page_token = None
        
        # Initial search
        params = {
            'query': query,
            'key': self.api_key,
            'fields': 'place_id,name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,business_status,geometry'
        }
        
        if location:
            # Geocode the location first for location bias
            geocode_result = self._geocode(location)
            if geocode_result:
                params['location'] = f"{geocode_result['lat']},{geocode_result['lng']}"
                params['radius'] = 50000  # 50km radius
        
        try:
            while len(businesses) < max_results:
                if next_page_token:
                    params['pagetoken'] = next_page_token
                    time.sleep(2)  # Required delay for next page token
                
                response = requests.get(f"{self.base_url}/textsearch/json", params=params)
                response.raise_for_status()
                data = response.json()
                
                if data['status'] != 'OK' and data['status'] != 'ZERO_RESULTS':
                    raise Exception(f"API Error: {data.get('error_message', data['status'])}")
                
                if 'results' in data:
                    for place in data['results']:
                        if len(businesses) >= max_results:
                            break
                        
                        # Get detailed info including website
                        detailed_info = self.get_place_details(place['place_id'])
                        if detailed_info:
                            businesses.append(detailed_info)
                
                # Check for next page
                next_page_token = data.get('next_page_token')
                if not next_page_token:
                    break
                
                # Remove pagetoken from params for next iteration
                params.pop('pagetoken', None)
        
        except Exception as e:
            print(f"Error in search_by_text: {e}")
            raise
        
        return businesses
    
    def search_nearby(self, lat: float, lng: float, keyword: str, radius: int = 10000, max_results: int = 60) -> List[Dict]:
        """
        Search for places near a location using coordinates.
        
        Args:
            lat: Latitude
            lng: Longitude
            keyword: Business type keyword (e.g., "plumber", "hotel")
            radius: Search radius in meters (default 10km = 10000m)
            max_results: Maximum number of results
            
        Returns:
            List of business dictionaries
        """
        businesses = []
        next_page_token = None
        
        params = {
            'location': f"{lat},{lng}",
            'radius': radius,
            'keyword': keyword,
            'key': self.api_key
        }
        
        try:
            while len(businesses) < max_results:
                if next_page_token:
                    params['pagetoken'] = next_page_token
                    time.sleep(2)
                
                response = requests.get(f"{self.base_url}/nearbysearch/json", params=params)
                response.raise_for_status()
                data = response.json()
                
                if data['status'] != 'OK' and data['status'] != 'ZERO_RESULTS':
                    raise Exception(f"API Error: {data.get('error_message', data['status'])}")
                
                if 'results' in data:
                    for place in data['results']:
                        if len(businesses) >= max_results:
                            break
                        
                        # Get detailed info
                        detailed_info = self.get_place_details(place['place_id'])
                        if detailed_info:
                            businesses.append(detailed_info)
                
                next_page_token = data.get('next_page_token')
                if not next_page_token:
                    break
                
                params.pop('pagetoken', None)
        
        except Exception as e:
            print(f"Error in search_nearby: {e}")
            raise
        
        return businesses
    
    def get_place_details(self, place_id: str) -> Optional[Dict]:
        """
        Get detailed information about a place including website.
        
        Args:
            place_id: Google Places place_id
            
        Returns:
            Dictionary with business details or None
        """
        params = {
            'place_id': place_id,
            'key': self.api_key,
            'fields': 'name,formatted_address,formatted_phone_number,website,rating,user_ratings_total,business_status,geometry,types,opening_hours,price_level'
        }
        
        try:
            response = requests.get(f"{self.base_url}/details/json", params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] != 'OK':
                return None
            
            result = data.get('result', {})
            
            return {
                'place_id': place_id,
                'name': result.get('name', ''),
                'address': result.get('formatted_address', ''),
                'phone': result.get('formatted_phone_number', ''),
                'website': result.get('website', ''),
                'has_website': bool(result.get('website')),
                'rating': result.get('rating'),
                'total_ratings': result.get('user_ratings_total', 0),
                'business_status': result.get('business_status', ''),
                'latitude': result.get('geometry', {}).get('location', {}).get('lat'),
                'longitude': result.get('geometry', {}).get('location', {}).get('lng'),
                'types': result.get('types', []),
                'opening_hours': result.get('opening_hours', {}).get('weekday_text', []),
                'price_level': result.get('price_level')
            }
        
        except Exception as e:
            print(f"Error getting place details: {e}")
            return None
    
    def _geocode(self, address: str) -> Optional[Dict]:
        """Geocode an address to get coordinates"""
        params = {
            'address': address,
            'key': self.api_key
        }
        
        try:
            response = requests.get("https://maps.googleapis.com/maps/api/geocode/json", params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['status'] == 'OK' and data['results']:
                location = data['results'][0]['geometry']['location']
                return {'lat': location['lat'], 'lng': location['lng']}
        except:
            pass
        
        return None
    
    def filter_businesses_without_website(self, businesses: List[Dict]) -> List[Dict]:
        """Filter businesses that don't have a website"""
        return [b for b in businesses if not b.get('has_website', False)]

