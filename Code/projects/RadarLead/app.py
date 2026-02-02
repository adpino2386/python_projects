"""
RadarLead Web Application
A web app for finding businesses without websites using Google Places API
"""
from flask import Flask, render_template, request, jsonify, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from dotenv import load_dotenv
from services.places_service import PlacesService
from utils.connection_engine import create_connection_postgresql

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Use PostgreSQL connection
try:
    engine = create_connection_postgresql()
    # Use the engine's URL (SQLAlchemy handles encoding properly)
    app.config['SQLALCHEMY_DATABASE_URI'] = str(engine.url)
    print("✅ Flask app configured with PostgreSQL")
except Exception as e:
    print(f"⚠️  Error connecting to PostgreSQL: {e}")
    print("   Falling back to SQLite for development...")
    print("   Run 'python test_db_connection.py' to troubleshoot PostgreSQL connection")
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///radarlead.db'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
    'pool_pre_ping': True,  # Verify connections before using
    'pool_recycle': 300,    # Recycle connections after 5 minutes
}

db = SQLAlchemy(app)

# Initialize Places Service
try:
    places_service = PlacesService()
except ValueError as e:
    print(f"Warning: {e}. Please set GOOGLE_PLACES_API_KEY environment variable.")
    places_service = None


# Database Models
class SearchQuery(db.Model):
    """Store search queries"""
    id = db.Column(db.Integer, primary_key=True)
    business_type = db.Column(db.String(200), nullable=False)
    location = db.Column(db.String(500), nullable=False)
    search_type = db.Column(db.String(50), nullable=False)  # 'text' or 'nearby'
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    radius = db.Column(db.Integer, nullable=True)  # in meters
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    results_count = db.Column(db.Integer, default=0)
    businesses_without_website = db.Column(db.Integer, default=0)
    
    # Relationship
    businesses = db.relationship('Business', backref='search_query', lazy=True, cascade='all, delete-orphan')


class Business(db.Model):
    """Store business information"""
    id = db.Column(db.Integer, primary_key=True)
    search_query_id = db.Column(db.Integer, db.ForeignKey('search_query.id'), nullable=False)
    place_id = db.Column(db.String(200), unique=True, nullable=False)
    name = db.Column(db.String(500), nullable=False)
    address = db.Column(db.Text, nullable=True)
    phone = db.Column(db.String(50), nullable=True)
    website = db.Column(db.String(500), nullable=True)
    has_website = db.Column(db.Boolean, default=False)
    rating = db.Column(db.Float, nullable=True)
    total_ratings = db.Column(db.Integer, default=0)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    business_status = db.Column(db.String(50), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


# Routes
@app.route('/')
def index():
    """Home page"""
    return render_template('index.html')


@app.route('/api/search', methods=['POST'])
def search_businesses():
    """API endpoint for searching businesses"""
    if not places_service:
        return jsonify({'error': 'Google Places API key not configured'}), 500
    
    data = request.json
    business_type = data.get('business_type', '').strip()
    location = data.get('location', '').strip()
    search_type = data.get('search_type', 'text')  # 'text' or 'nearby'
    latitude = data.get('latitude')
    longitude = data.get('longitude')
    radius = data.get('radius', 10000)  # Default 10km
    
    if not business_type:
        return jsonify({'error': 'Business type is required'}), 400
    
    try:
        if search_type == 'nearby':
            if not latitude or not longitude:
                return jsonify({'error': 'Latitude and longitude are required for nearby search'}), 400
            
            businesses = places_service.search_nearby(
                lat=float(latitude),
                lng=float(longitude),
                keyword=business_type,
                radius=int(radius),
                max_results=60
            )
            location_str = f"Lat: {latitude}, Lng: {longitude}"
        else:
            if not location:
                return jsonify({'error': 'Location is required for text search'}), 400
            
            query = f"{business_type} in {location}"
            businesses = places_service.search_by_text(query, location=location, max_results=60)
            location_str = location
        
        # Filter businesses without websites
        businesses_without_website = places_service.filter_businesses_without_website(businesses)
        
        # Store in database
        search_query = SearchQuery(
            business_type=business_type,
            location=location_str,
            search_type=search_type,
            latitude=float(latitude) if latitude else None,
            longitude=float(longitude) if longitude else None,
            radius=int(radius) if radius else None,
            results_count=len(businesses),
            businesses_without_website=len(businesses_without_website)
        )
        db.session.add(search_query)
        db.session.flush()
        
        # Store businesses
        for biz in businesses:
            business = Business(
                search_query_id=search_query.id,
                place_id=biz.get('place_id', ''),
                name=biz.get('name', ''),
                address=biz.get('address', ''),
                phone=biz.get('phone', ''),
                website=biz.get('website', ''),
                has_website=biz.get('has_website', False),
                rating=biz.get('rating'),
                total_ratings=biz.get('total_ratings', 0),
                latitude=biz.get('latitude'),
                longitude=biz.get('longitude'),
                business_status=biz.get('business_status', '')
            )
            db.session.add(business)
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'total_businesses': len(businesses),
            'businesses_without_website': len(businesses_without_website),
            'businesses': businesses_without_website,  # Return only those without websites
            'search_id': search_query.id
        })
    
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500


@app.route('/api/searches', methods=['GET'])
def get_searches():
    """Get all past searches"""
    searches = SearchQuery.query.order_by(SearchQuery.created_at.desc()).limit(50).all()
    return jsonify([{
        'id': s.id,
        'business_type': s.business_type,
        'location': s.location,
        'search_type': s.search_type,
        'created_at': s.created_at.isoformat(),
        'results_count': s.results_count,
        'businesses_without_website': s.businesses_without_website
    } for s in searches])


@app.route('/api/search/<int:search_id>/businesses', methods=['GET'])
def get_businesses(search_id):
    """Get businesses for a specific search"""
    only_without_website = request.args.get('without_website', 'false').lower() == 'true'
    
    query = Business.query.filter_by(search_query_id=search_id)
    if only_without_website:
        query = query.filter_by(has_website=False)
    
    businesses = query.all()
    return jsonify([{
        'id': b.id,
        'name': b.name,
        'address': b.address,
        'phone': b.phone,
        'website': b.website,
        'has_website': b.has_website,
        'rating': b.rating,
        'total_ratings': b.total_ratings,
        'latitude': b.latitude,
        'longitude': b.longitude
    } for b in businesses])


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True, port=5000)

