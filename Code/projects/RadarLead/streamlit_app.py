"""
RadarLead Streamlit Web Application
A simple web app for finding businesses without websites using Google Places API
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from services.places_service import PlacesService
from utils.connection_engine import create_connection_postgresql
from sqlalchemy import text
import json

# Page config
st.set_page_config(
    page_title="RadarLead - Find Businesses Without Websites",
    page_icon="🔍",
    layout="wide"
)

# Load environment variables
load_dotenv()

# Initialize session state
if 'places_service' not in st.session_state:
    try:
        st.session_state.places_service = PlacesService()
    except ValueError as e:
        st.error(f"⚠️ Google Places API key not configured: {e}")
        st.session_state.places_service = None
        st.stop()

if 'db_engine' not in st.session_state:
    try:
        st.session_state.db_engine = create_connection_postgresql()
    except Exception as e:
        st.warning(f"⚠️ Could not connect to PostgreSQL: {e}")
        st.warning("Data will not be saved to database.")
        st.session_state.db_engine = None

# Initialize database tables if engine is available
if st.session_state.db_engine:
    try:
        with st.session_state.db_engine.connect() as conn:
            # Create tables if they don't exist
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS search_queries (
                    id SERIAL PRIMARY KEY,
                    business_type VARCHAR(200) NOT NULL,
                    location VARCHAR(500) NOT NULL,
                    search_type VARCHAR(50) NOT NULL,
                    latitude FLOAT,
                    longitude FLOAT,
                    radius INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    results_count INTEGER DEFAULT 0,
                    businesses_without_website INTEGER DEFAULT 0
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS businesses (
                    id SERIAL PRIMARY KEY,
                    search_query_id INTEGER REFERENCES search_queries(id) ON DELETE CASCADE,
                    place_id VARCHAR(200) UNIQUE NOT NULL,
                    name VARCHAR(500) NOT NULL,
                    address TEXT,
                    phone VARCHAR(50),
                    website VARCHAR(500),
                    has_website BOOLEAN DEFAULT FALSE,
                    rating FLOAT,
                    total_ratings INTEGER DEFAULT 0,
                    latitude FLOAT,
                    longitude FLOAT,
                    business_status VARCHAR(50),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            conn.commit()
    except Exception as e:
        st.warning(f"⚠️ Database initialization error: {e}")

# Main UI
st.title("🔍 RadarLead")
st.markdown("### Find businesses without websites in your area")

# Sidebar for search options
with st.sidebar:
    st.header("Search Options")
    search_type = st.radio(
        "Search Type",
        ["📍 By Location", "🗺️ By Coordinates"],
        help="Choose how to search for businesses"
    )

# Main search form
with st.form("search_form"):
    col1, col2 = st.columns(2)
    
    with col1:
        business_type = st.text_input(
            "Business Type *",
            placeholder="e.g., Plumbers, Hotels, Restaurants",
            help="Type of business to search for"
        )
    
    if search_type == "📍 By Location":
        with col2:
            location = st.text_input(
                "Location *",
                placeholder="e.g., Montreal, Quebec, Canada",
                help="City, province/state, and country"
            )
        latitude = None
        longitude = None
        radius = None
    else:
        with col2:
            col_lat, col_lng = st.columns(2)
            with col_lat:
                latitude = st.number_input(
                    "Latitude *",
                    value=45.5017,
                    format="%.4f"
                )
            with col_lng:
                longitude = st.number_input(
                    "Longitude *",
                    value=-73.5673,
                    format="%.4f"
                )
        radius = st.number_input(
            "Search Radius (meters)",
            min_value=1000,
            max_value=50000,
            value=10000,
            step=1000,
            help="Search radius in meters (default: 10km)"
        )
        location = None
    
    submitted = st.form_submit_button("🔍 Search Businesses", use_container_width=True)

# Process search
if submitted:
    if not business_type:
        st.error("❌ Business type is required!")
    elif search_type == "📍 By Location" and not location:
        st.error("❌ Location is required!")
    elif search_type == "🗺️ By Coordinates" and (not latitude or not longitude):
        st.error("❌ Latitude and longitude are required!")
    else:
        with st.spinner("🔍 Searching for businesses..."):
            try:
                if search_type == "🗺️ By Coordinates":
                    businesses = st.session_state.places_service.search_nearby(
                        lat=float(latitude),
                        lng=float(longitude),
                        keyword=business_type,
                        radius=int(radius),
                        max_results=60
                    )
                    location_str = f"Lat: {latitude}, Lng: {longitude}"
                else:
                    query = f"{business_type} in {location}"
                    businesses = st.session_state.places_service.search_by_text(
                        query, 
                        location=location, 
                        max_results=60
                    )
                    location_str = location
                
                # Filter businesses without websites
                businesses_without_website = st.session_state.places_service.filter_businesses_without_website(businesses)
                
                # Store in database if engine is available
                search_query_id = None
                if st.session_state.db_engine:
                    try:
                        with st.session_state.db_engine.connect() as conn:
                            # Insert search query
                            result = conn.execute(text("""
                                INSERT INTO search_queries 
                                (business_type, location, search_type, latitude, longitude, radius, results_count, businesses_without_website)
                                VALUES (:business_type, :location, :search_type, :latitude, :longitude, :radius, :results_count, :businesses_without_website)
                                RETURNING id
                            """), {
                                'business_type': business_type,
                                'location': location_str,
                                'search_type': 'nearby' if search_type == "🗺️ By Coordinates" else 'text',
                                'latitude': float(latitude) if latitude else None,
                                'longitude': float(longitude) if longitude else None,
                                'radius': int(radius) if radius else None,
                                'results_count': len(businesses),
                                'businesses_without_website': len(businesses_without_website)
                            })
                            search_query_id = result.fetchone()[0]
                            
                            # Insert businesses
                            for biz in businesses:
                                conn.execute(text("""
                                    INSERT INTO businesses 
                                    (search_query_id, place_id, name, address, phone, website, has_website, rating, total_ratings, latitude, longitude, business_status)
                                    VALUES (:search_query_id, :place_id, :name, :address, :phone, :website, :has_website, :rating, :total_ratings, :latitude, :longitude, :business_status)
                                    ON CONFLICT (place_id) DO NOTHING
                                """), {
                                    'search_query_id': search_query_id,
                                    'place_id': biz.get('place_id', ''),
                                    'name': biz.get('name', ''),
                                    'address': biz.get('address', ''),
                                    'phone': biz.get('phone', ''),
                                    'website': biz.get('website', ''),
                                    'has_website': biz.get('has_website', False),
                                    'rating': biz.get('rating'),
                                    'total_ratings': biz.get('total_ratings', 0),
                                    'latitude': biz.get('latitude'),
                                    'longitude': biz.get('longitude'),
                                    'business_status': biz.get('business_status', '')
                                })
                            conn.commit()
                    except Exception as e:
                        st.warning(f"⚠️ Could not save to database: {e}")
                
                # Display results
                st.success(f"✅ Found {len(businesses)} businesses, {len(businesses_without_website)} without websites!")
                
                if businesses_without_website:
                    # Create DataFrame for display
                    df = pd.DataFrame(businesses_without_website)
                    
                    # Display summary
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Total Businesses", len(businesses))
                    with col2:
                        st.metric("Without Websites", len(businesses_without_website))
                    with col3:
                        st.metric("With Websites", len(businesses) - len(businesses_without_website))
                    
                    # Display table
                    st.subheader("📋 Businesses Without Websites")
                    
                    # Prepare display columns
                    display_df = df[['name', 'address', 'phone', 'rating', 'total_ratings']].copy()
                    display_df.columns = ['Name', 'Address', 'Phone', 'Rating', 'Reviews']
                    display_df = display_df.fillna('N/A')
                    
                    st.dataframe(display_df, use_container_width=True, hide_index=True)
                    
                    # Export options
                    st.subheader("📥 Export Results")
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        csv = df.to_csv(index=False)
                        st.download_button(
                            label="📄 Download CSV",
                            data=csv,
                            file_name=f"businesses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                            mime="text/csv"
                        )
                    
                    with col2:
                        json_str = json.dumps(businesses_without_website, indent=2)
                        st.download_button(
                            label="📄 Download JSON",
                            data=json_str,
                            file_name=f"businesses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                else:
                    st.info("ℹ️ No businesses without websites found in this area.")
                    
            except Exception as e:
                st.error(f"❌ Error searching businesses: {e}")
                import traceback
                st.code(traceback.format_exc())

# Show past searches if database is available
if st.session_state.db_engine:
    with st.expander("📊 View Past Searches"):
        try:
            with st.session_state.db_engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, business_type, location, search_type, created_at, results_count, businesses_without_website
                    FROM search_queries
                    ORDER BY created_at DESC
                    LIMIT 20
                """))
                searches = result.fetchall()
                
                if searches:
                    searches_df = pd.DataFrame(searches, columns=[
                        'ID', 'Business Type', 'Location', 'Search Type', 'Created At', 'Total Results', 'Without Websites'
                    ])
                    st.dataframe(searches_df, use_container_width=True, hide_index=True)
                else:
                    st.info("No past searches found.")
        except Exception as e:
            st.warning(f"Could not load past searches: {e}")

