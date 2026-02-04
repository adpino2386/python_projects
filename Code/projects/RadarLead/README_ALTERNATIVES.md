# Free Alternatives to Google Places API

## Overview

Google Places API has a free tier ($200/month credit), but if you want completely free alternatives, here are your options:

## 1. OpenStreetMap (OSM) - **100% FREE, No API Key**

### Pros:
- ✅ Completely free, no API key needed
- ✅ Open source and community-driven
- ✅ Good global coverage
- ✅ No usage limits (but be respectful with rate limiting)

### Cons:
- ❌ Less business data than Google (websites, ratings often missing)
- ❌ Slower than Google (rate limit: 1 request/second for Nominatim)
- ❌ Phone numbers not always available
- ❌ No price level information

### How it works:
- **Nominatim**: Geocoding (address → coordinates)
- **Overpass API**: Query businesses/POIs by location

### Example Usage:
```python
from services.osm_service import OSMService

osm = OSMService()

# Search businesses in Montreal
businesses = osm.search_businesses_by_location("Montreal, Quebec, Canada", "plumbers")

# Or search by coordinates
businesses = osm.search_businesses_nearby(45.5017, -73.5673, "hotels", radius=5000)
```

## 2. Foursquare Places API - **Free Tier Available**

### Pros:
- ✅ Good business data (websites, phone numbers)
- ✅ 100,000 free calls/day
- ✅ Reliable and fast

### Cons:
- ❌ Requires free API key
- ❌ Less coverage than Google in some areas

### Setup:
1. Sign up at [developer.foursquare.com](https://developer.foursquare.com)
2. Get free API key
3. 100,000 calls/day free tier

## 3. Yelp Fusion API - **Free Tier Available**

### Pros:
- ✅ Excellent business data
- ✅ Reviews and ratings included
- ✅ 5,000 free calls/day

### Cons:
- ❌ Requires free API key
- ❌ Mainly US/Canada coverage
- ❌ Lower free tier than Foursquare

### Setup:
1. Sign up at [yelp.com/developers](https://www.yelp.com/developers)
2. Get free API key
3. 5,000 calls/day free tier

## 4. Mapbox Geocoding API - **Free Tier Available**

### Pros:
- ✅ 100,000 free requests/month
- ✅ Fast and reliable
- ✅ Good for geocoding

### Cons:
- ❌ Limited business/POI data
- ❌ Requires free API key
- ❌ Better for geocoding than business search

## Comparison Table

| Service | Cost | API Key | Business Data | Website Info | Ratings | Coverage |
|---------|------|---------|---------------|--------------|---------|----------|
| **Google Places** | $200/mo free | ✅ Required | ⭐⭐⭐⭐⭐ | ✅ Yes | ✅ Yes | Global |
| **OpenStreetMap** | **FREE** | ❌ None | ⭐⭐⭐ | ⚠️ Sometimes | ❌ No | Global |
| **Foursquare** | **FREE** (100k/day) | ✅ Required | ⭐⭐⭐⭐ | ✅ Yes | ⚠️ Limited | Good |
| **Yelp** | **FREE** (5k/day) | ✅ Required | ⭐⭐⭐⭐⭐ | ✅ Yes | ✅ Yes | US/CA |
| **Mapbox** | **FREE** (100k/mo) | ✅ Required | ⭐⭐ | ❌ No | ❌ No | Global |

## Recommendation

**For your use case (finding businesses without websites):**

1. **Best Free Option**: **OpenStreetMap** - Completely free, no API key, works everywhere
   - Use the `osm_service.py` I created
   - Note: Website information may be incomplete

2. **Best Data Quality**: **Foursquare** - Free tier with good business data
   - Better website detection than OSM
   - Still requires API key (but free)

3. **Hybrid Approach**: Use OSM for location search, then check websites manually or use a secondary service

## Using the OSM Service

I've created `services/osm_service.py` that you can use as a drop-in replacement:

```python
# Instead of:
from services.places_service import PlacesService
service = PlacesService()

# Use:
from services.osm_service import OSMService
service = OSMService()

# Same interface:
businesses = service.search_businesses_by_location("Montreal", "plumbers")
businesses = service.search_businesses_nearby(lat, lng, "hotels", radius=5000)
```

**Note**: OSM data quality varies by region. Urban areas typically have better data than rural areas.

