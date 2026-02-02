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
import folium
from streamlit_folium import st_folium

# Page config
st.set_page_config(
    page_title="RadarLead - Find Businesses Without Websites",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Multi-page navigation
page = st.sidebar.selectbox(
    "Navigation",
    ["🔍 Search by Location/Coordinates", "🗺️ Search by Map"],
    index=0
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
                    price_level INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """))
            
            # Add price_level column if it doesn't exist (for existing databases)
            try:
                conn.execute(text("""
                    ALTER TABLE businesses 
                    ADD COLUMN IF NOT EXISTS price_level INTEGER
                """))
            except:
                pass  # Column might already exist
            conn.commit()
    except Exception as e:
        st.warning(f"⚠️ Database initialization error: {e}")

# Helper function to display results
def display_results(businesses, businesses_without_website):
    """Display business results with filters"""
    if not businesses:
        return
    
    # Initialize filter option in session state (before widget creation)
    if 'filter_option' not in st.session_state:
        st.session_state.filter_option = "All Businesses"
    
    # Display summary
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Businesses", len(businesses))
    with col2:
        st.metric("Without Websites", len(businesses_without_website))
    with col3:
        st.metric("With Websites", len(businesses) - len(businesses_without_website))
    with col4:
        avg_rating = pd.DataFrame(businesses)['rating'].mean()
        st.metric("Avg Rating", f"{avg_rating:.1f}" if not pd.isna(avg_rating) else "N/A")
    
    # Filter option
    st.subheader("📋 Business Results")
    # Get current filter option index
    filter_options = ["All Businesses", "Without Websites Only", "With Websites Only"]
    current_index = filter_options.index(st.session_state.filter_option) if st.session_state.filter_option in filter_options else 0
    
    # Create radio widget - it will automatically update session state
    filter_option = st.radio(
        "Show:",
        filter_options,
        horizontal=True,
        key="filter_option",
        index=current_index
    )
    # Don't set st.session_state.filter_option here - the widget does it automatically
    
    # Filter businesses based on selection
    if filter_option == "All Businesses":
        display_businesses = businesses
        filter_label = "All Businesses"
    elif filter_option == "Without Websites Only":
        display_businesses = businesses_without_website
        filter_label = "Businesses Without Websites"
    else:
        display_businesses = [b for b in businesses if b.get('has_website', False)]
        filter_label = "Businesses With Websites"
    
    if display_businesses:
        # Create DataFrame for display
        df = pd.DataFrame(display_businesses)
        
        # Prepare display columns with all requested fields
        display_columns = {
            'name': 'Name',
            'address': 'Address',
            'phone': 'Phone',
            'website': 'Website',
            'has_website': 'Has Website',
            'rating': 'Rating',
            'total_ratings': 'Reviews',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'price_level': 'Price Level'
        }
        
        # Select available columns
        available_cols = [col for col in display_columns.keys() if col in df.columns]
        display_df = df[available_cols].copy()
        display_df.columns = [display_columns[col] for col in available_cols]
        
        # Handle NaN values properly for display
        if 'Rating' in display_df.columns:
            display_df['Rating'] = pd.to_numeric(display_df['Rating'], errors='coerce')
        if 'Reviews' in display_df.columns:
            display_df['Reviews'] = pd.to_numeric(display_df['Reviews'], errors='coerce').fillna(0).astype(int)
        if 'Latitude' in display_df.columns:
            # Keep as numeric but format for display with full precision
            display_df['Latitude'] = pd.to_numeric(display_df['Latitude'], errors='coerce')
            # Store original numeric values for export, but display with full precision
            display_df['Latitude'] = display_df['Latitude'].apply(
                lambda x: f"{x:.10f}".rstrip('0').rstrip('.') if pd.notna(x) else ''
            )
        if 'Longitude' in display_df.columns:
            display_df['Longitude'] = pd.to_numeric(display_df['Longitude'], errors='coerce')
            display_df['Longitude'] = display_df['Longitude'].apply(
                lambda x: f"{x:.10f}".rstrip('0').rstrip('.') if pd.notna(x) else ''
            )
        
        # Format price level
        if 'Price Level' in display_df.columns:
            price_map = {0: 'Free', 1: 'Inexpensive', 2: 'Moderate', 3: 'Expensive', 4: 'Very Expensive'}
            display_df['Price Level'] = display_df['Price Level'].map(price_map).fillna('Not Available')
        
        # Format Has Website column
        if 'Has Website' in display_df.columns:
            display_df['Has Website'] = display_df['Has Website'].map({True: 'Yes', False: 'No'})
        
        # Fill remaining NaN with empty string for string columns
        for col in display_df.columns:
            if display_df[col].dtype == 'object':
                display_df[col] = display_df[col].fillna('')
        
        st.dataframe(display_df, width='stretch', hide_index=True)
        
        # Export options
        st.subheader("📥 Export Results")
        col1, col2 = st.columns(2)
        
        # Prepare export data (use original numeric values)
        export_df = pd.DataFrame(display_businesses)
        
        with col1:
            csv = export_df.to_csv(index=False)
            st.download_button(
                label="📄 Download CSV",
                data=csv,
                file_name=f"businesses_{filter_option.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
        
        with col2:
            json_str = json.dumps(display_businesses, indent=2, default=str)
            st.download_button(
                label="📄 Download JSON",
                data=json_str,
                file_name=f"businesses_{filter_option.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json"
            )
    else:
        st.info(f"ℹ️ No {filter_label.lower()} found in this area.")

# Main content based on selected page
if page == "🔍 Search by Location/Coordinates":
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
                        format="%.10f"
                    )
                with col_lng:
                    longitude = st.number_input(
                        "Longitude *",
                        value=-73.5673,
                        format="%.10f"
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
        
        submitted = st.form_submit_button("🔍 Search Businesses", use_container_width=True, type="primary")
    
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
                                        (search_query_id, place_id, name, address, phone, website, has_website, rating, total_ratings, latitude, longitude, business_status, price_level)
                                        VALUES (:search_query_id, :place_id, :name, :address, :phone, :website, :has_website, :rating, :total_ratings, :latitude, :longitude, :business_status, :price_level)
                                        ON CONFLICT (place_id) DO UPDATE SET
                                            rating = EXCLUDED.rating,
                                            total_ratings = EXCLUDED.total_ratings,
                                            price_level = EXCLUDED.price_level
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
                                        'business_status': biz.get('business_status', ''),
                                        'price_level': biz.get('price_level')
                                    })
                                conn.commit()
                        except Exception as e:
                            st.warning(f"⚠️ Could not save to database: {e}")
                    
                    # Store results in session state
                    st.session_state.businesses = businesses
                    st.session_state.businesses_without_website = businesses_without_website
                    st.session_state.filter_option = "All Businesses"
                    
                    # Display results
                    st.success(f"✅ Found {len(businesses)} businesses, {len(businesses_without_website)} without websites!")
                    
                except Exception as e:
                    st.error(f"❌ Error searching businesses: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Show results if they exist in session state (persists when filter changes)
    if 'businesses' in st.session_state and st.session_state.businesses:
        display_results(st.session_state.businesses, st.session_state.businesses_without_website)

elif page == "🗺️ Search by Map":
    st.title("🗺️ Interactive Map Search")
    st.markdown("### Click on the map to search for businesses in that area")
    
    # Business type input
    business_type_map = st.text_input(
        "Business Type *",
        placeholder="e.g., Hotels, Restaurants, Plumbers",
        help="Type of business to search for",
        key="map_business_type"
    )
    
    # Radius selection
    col1, col2 = st.columns([3, 1])
    with col1:
        radius_km = st.slider(
            "Search Radius (kilometers)",
            min_value=1,
            max_value=20,
            value=5,
            step=1,
            help="Radius around the selected point to search for businesses"
        )
    with col2:
        radius_meters = radius_km * 1000
        st.metric("Radius", f"{radius_meters:,} m")
    
    # Initialize map center (default to Montreal) - only set if not already set
    # IMPORTANT: Never reset this once it's been set by user interaction
    if 'map_center' not in st.session_state:
        st.session_state.map_center = [45.5017, -73.5673]  # Montreal
    
    # Store the current map center to use for search (persist through operations)
    # Always use session state directly - never reset it
    current_map_center = st.session_state.map_center.copy()
    
    # Create interactive map with Folium
    st.subheader("📍 Click on the map to select a location")
    st.info("💡 **Click anywhere on the map to select that location, or enter coordinates manually below.**")
    
    # Create Folium map using current center
    m = folium.Map(
        location=current_map_center,
        zoom_start=10,
        tiles='OpenStreetMap'
    )
    
    # Add marker for selected location
    marker = folium.Marker(
        current_map_center,
        popup=f"Selected Location<br>Lat: {current_map_center[0]:.6f}<br>Lng: {current_map_center[1]:.6f}",
        tooltip="Selected Location - Click map to change",
        icon=folium.Icon(color='red', icon='info-sign')
    )
    marker.add_to(m)
    
    # Display map and get clicked location
    # st_folium automatically captures clicks - use a stable key
    map_data = st_folium(
        m, 
        width='100%', 
        height=500, 
        returned_objects=["last_clicked"],
        key="interactive_map"
    )
    
    # Get clicked coordinates from map
    if map_data and map_data.get("last_clicked"):
        clicked_lat = map_data["last_clicked"]["lat"]
        clicked_lng = map_data["last_clicked"]["lng"]
        
        # Check if this is a new click (different from current center)
        current_lat = current_map_center[0]
        current_lng = current_map_center[1]
        
        # Update if clicked location is significantly different
        threshold = 0.0001  # About 10 meters
        lat_diff = abs(clicked_lat - current_lat)
        lng_diff = abs(clicked_lng - current_lng)
        
        if lat_diff > threshold or lng_diff > threshold:
            st.session_state.map_center = [clicked_lat, clicked_lng]
            st.success(f"📍 Location updated! Lat: {clicked_lat:.6f}, Lng: {clicked_lng:.6f}")
            st.rerun()
    
    # Show current selected coordinates with update buttons
    st.subheader("📍 Selected Location Coordinates")
    col1, col2, col3 = st.columns([2, 2, 1])
    with col1:
        map_lat = st.number_input(
            "Latitude",
            value=current_map_center[0],
            format="%.10f",
            step=0.0001,
            key="map_lat_input"
        )
    with col2:
        map_lng = st.number_input(
            "Longitude",
            value=current_map_center[1],
            format="%.10f",
            step=0.0001,
            key="map_lng_input"
        )
    with col3:
        st.write("")  # Spacing
        st.write("")  # Spacing
        update_coords = st.button("📍 Update Map", type="secondary")
    
    # Update map center when coordinates change manually or button clicked
    if update_coords:
        st.session_state.map_center = [map_lat, map_lng]
        st.rerun()
    
    # Use the session state map_center for search (not the input fields which might be stale)
    # This ensures we always use the most recent clicked/updated location
    # IMPORTANT: Get these values right before the search to ensure we have the latest
    search_lat = st.session_state.map_center[0]
    search_lng = st.session_state.map_center[1]
    
    # Display current search location
    st.info(f"📍 **Search will use:** Lat: {search_lat:.6f}, Lng: {search_lng:.6f}")
    
    # Search button
    if st.button("🔍 Search Businesses at This Location", type="primary", use_container_width=True):
        if not business_type_map:
            st.error("❌ Business type is required!")
        else:
            # Get the coordinates again right before search to ensure we have the latest
            final_search_lat = st.session_state.map_center[0]
            final_search_lng = st.session_state.map_center[1]
            
            with st.spinner(f"🔍 Searching for {business_type_map} within {radius_km}km at ({final_search_lat:.6f}, {final_search_lng:.6f})..."):
                try:
                    businesses = st.session_state.places_service.search_nearby(
                        lat=float(final_search_lat),
                        lng=float(final_search_lng),
                        keyword=business_type_map,
                        radius=int(radius_meters),
                        max_results=60
                    )
                    
                    if businesses:
                        # Store in session state
                        st.session_state.businesses = businesses
                        st.session_state.businesses_without_website = st.session_state.places_service.filter_businesses_without_website(businesses)
                        st.session_state.filter_option = "All Businesses"
                        # IMPORTANT: Preserve the map center after search
                        st.session_state.map_center = [final_search_lat, final_search_lng]
                        # Store search location for results map
                        st.session_state.search_location = [final_search_lat, final_search_lng]
                        
                        st.success(f"✅ Found {len(businesses)} businesses!")
                        st.rerun()  # Rerun to show the persistent map and table below
                    else:
                        st.warning(f"No {business_type_map} found in the selected area.")
                        
                except Exception as e:
                    st.error(f"❌ Error searching businesses: {e}")
                    import traceback
                    st.code(traceback.format_exc())
    
    # Show results map and table if they exist (persist after search)
    if 'businesses' in st.session_state and st.session_state.businesses and 'search_location' in st.session_state:
        businesses = st.session_state.businesses
        businesses_without_website = st.session_state.businesses_without_website
        search_loc = st.session_state.search_location
        
        # Show results on map
        st.subheader("📍 Results on Map")
        results_map = folium.Map(
            location=search_loc,
            zoom_start=12
        )
        
        # Add center marker
        folium.Marker(
            search_loc,
            popup=f"<b>Search Center</b><br>Lat: {search_loc[0]:.6f}<br>Lng: {search_loc[1]:.6f}",
            tooltip="Search Center",
            icon=folium.Icon(color='red', icon='info-sign', prefix='fa')
        ).add_to(results_map)
        
        # Add business markers
        for biz in businesses:
            if biz.get('latitude') and biz.get('longitude'):
                color = 'green' if biz.get('has_website') else 'blue'
                icon_type = 'check' if biz.get('has_website') else 'question'
                popup_html = f"""
                <b>{biz.get('name', 'Unknown')}</b><br>
                {'✅ Has Website' if biz.get('has_website') else '❌ No Website'}<br>
                Rating: {biz.get('rating', 'N/A')}<br>
                {biz.get('address', '')}
                """
                folium.Marker(
                    [biz.get('latitude'), biz.get('longitude')],
                    popup=folium.Popup(popup_html, max_width=300),
                    tooltip=biz.get('name', 'Unknown'),
                    icon=folium.Icon(color=color, icon=icon_type, prefix='fa')
                ).add_to(results_map)
        
        # Display the map with a stable key so it persists
        st_folium(results_map, width='100%', height=500, key="persistent_results_map")
        
        # Display results table
        st.subheader("📋 Business Details")
        display_results(businesses, businesses_without_website)

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
                    st.dataframe(searches_df, width='stretch', hide_index=True)
                else:
                    st.info("No past searches found.")
        except Exception as e:
            st.warning(f"Could not load past searches: {e}")
