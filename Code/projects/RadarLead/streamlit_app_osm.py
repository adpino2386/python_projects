"""
RadarLead Streamlit Web Application (OpenStreetMap Version - FREE, No API Key)
A simple web app for finding businesses without websites using OpenStreetMap
This version is completely FREE and requires NO API keys!
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os
from dotenv import load_dotenv
from services.osm_service import OSMService
import json
import folium
from streamlit_folium import st_folium

# Page config
st.set_page_config(
    page_title="RadarLead - Find Businesses Without Websites (Free OSM Version)",
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

# Load environment variables (not required for OSM, but kept for consistency)
load_dotenv()

# Initialize session state
if 'osm_service' not in st.session_state:
    try:
        st.session_state.osm_service = OSMService()
        st.sidebar.success("✅ Using OpenStreetMap (FREE, No API key needed!)")
    except Exception as e:
        st.error(f"⚠️ Error initializing OSM service: {e}")
        st.session_state.osm_service = None
        st.stop()

# Helper function to display results
def display_results(businesses, businesses_without_website):
    """Display business results with filters"""
    if not businesses:
        return
    
    # Initialize filter option in session state (before widget creation)
    if 'filter_option' not in st.session_state:
        st.session_state.filter_option = "All Businesses"
    
    # Display summary
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Businesses", len(businesses))
    with col2:
        st.metric("Without Websites", len(businesses_without_website))
    with col3:
        st.metric("With Websites", len(businesses) - len(businesses_without_website))
    
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
        
        # Prepare display columns (OSM has different fields than Google Places)
        display_columns = {
            'name': 'Name',
            'address': 'Address',
            'phone': 'Phone',
            'website': 'Website',
            'has_website': 'Has Website',
            'latitude': 'Latitude',
            'longitude': 'Longitude',
            'business_type': 'Business Type'
        }
        
        # Select available columns
        available_cols = [col for col in display_columns.keys() if col in df.columns]
        display_df = df[available_cols].copy()
        display_df.columns = [display_columns[col] for col in available_cols]
        
        # Handle NaN values properly for display
        if 'Latitude' in display_df.columns:
            display_df['Latitude'] = pd.to_numeric(display_df['Latitude'], errors='coerce')
            display_df['Latitude'] = display_df['Latitude'].apply(
                lambda x: f"{x:.10f}".rstrip('0').rstrip('.') if pd.notna(x) else ''
            )
        if 'Longitude' in display_df.columns:
            display_df['Longitude'] = pd.to_numeric(display_df['Longitude'], errors='coerce')
            display_df['Longitude'] = display_df['Longitude'].apply(
                lambda x: f"{x:.10f}".rstrip('0').rstrip('.') if pd.notna(x) else ''
            )
        
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

# Main UI
st.title("🔍 RadarLead (Free OSM Version)")
st.markdown("### Find businesses without websites using OpenStreetMap - **100% FREE, No API Key Required!**")
st.info("💡 **This version uses OpenStreetMap data. Website information may be incomplete compared to Google Places.**")

# Main content based on selected page
if page == "🔍 Search by Location/Coordinates":
    st.markdown("#### Search by Location or Coordinates")
    
    # Sidebar for search options
    with st.sidebar:
        st.header("Search Options")
        search_type = st.radio(
            "Search Type",
            ["📍 By Location", "🗺️ By Coordinates"],
            help="Choose how to search for businesses"
        )
        st.info("🌍 Using OpenStreetMap - Free & Open Source")
    
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
                value=5000,
                step=1000,
                help="Search radius in meters (default: 5km for better accuracy)"
            )
            location = None
        else:
            # For location-based search, also add radius option
            radius = st.number_input(
                "Search Radius (meters)",
                min_value=1000,
                max_value=50000,
                value=5000,
                step=1000,
                help="Search radius in meters (default: 5km for better accuracy)"
            )
        
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
            with st.spinner("🔍 Searching OpenStreetMap for businesses... (This may take a few seconds)"):
                try:
                    if search_type == "🗺️ By Coordinates":
                        businesses = st.session_state.osm_service.search_businesses_nearby(
                            lat=float(latitude),
                            lng=float(longitude),
                            business_type=business_type,
                            radius=int(radius)
                        )
                    else:
                        businesses = st.session_state.osm_service.search_businesses_by_location(
                            location=location,
                            business_type=business_type,
                            radius=int(radius) if radius else 5000
                        )
                    
                    # Filter businesses without websites
                    businesses_without_website = st.session_state.osm_service.filter_businesses_without_website(businesses)
                    
                    # Store results in session state
                    st.session_state.businesses = businesses
                    st.session_state.businesses_without_website = businesses_without_website
                    st.session_state.filter_option = "All Businesses"
                    
                    # Display results
                    st.success(f"✅ Found {len(businesses)} businesses, {len(businesses_without_website)} without websites!")
                    
                    if len(businesses) == 0:
                        st.warning("⚠️ No businesses found. Try:")
                        st.markdown("- Different business type keywords")
                        st.markdown("- Larger search radius")
                        st.markdown("- Different location")
                        st.info("💡 OSM data quality varies by region. Urban areas typically have better coverage.")
                    
                except Exception as e:
                    st.error(f"❌ Error searching businesses: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    st.info("💡 OSM services may be temporarily unavailable. Please try again in a moment.")
    
    # Show results if they exist in session state (persists when filter changes)
    if 'businesses' in st.session_state and st.session_state.businesses:
        display_results(st.session_state.businesses, st.session_state.businesses_without_website)

elif page == "🗺️ Search by Map":
    st.title("🗺️ Interactive Map Search")
    st.markdown("### Click on the map to search for businesses in that area")
    st.info("💡 **This version uses OpenStreetMap data. Website information may be incomplete compared to Google Places.**")
    
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
    
    # Update map center when button clicked
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
            
            with st.spinner(f"🔍 Searching OpenStreetMap for {business_type_map} within {radius_km}km... (This may take a few seconds)"):
                try:
                    businesses = st.session_state.osm_service.search_businesses_nearby(
                        lat=float(final_search_lat),
                        lng=float(final_search_lng),
                        business_type=business_type_map,
                        radius=int(radius_meters)
                    )
                    
                    if businesses:
                        # Store in session state
                        st.session_state.businesses = businesses
                        st.session_state.businesses_without_website = st.session_state.osm_service.filter_businesses_without_website(businesses)
                        st.session_state.filter_option = "All Businesses"
                        # IMPORTANT: Preserve the map center after search
                        st.session_state.map_center = [final_search_lat, final_search_lng]
                        # Store search location for results map
                        st.session_state.search_location = [final_search_lat, final_search_lng]
                        
                        st.success(f"✅ Found {len(businesses)} businesses!")
                        st.rerun()  # Rerun to show the persistent map and table below
                    else:
                        st.warning(f"No {business_type_map} found in the selected area.")
                        st.info("💡 OSM data quality varies by region. Try:")
                        st.markdown("- Different business type keywords")
                        st.markdown("- Larger search radius")
                        st.markdown("- Different location")
                        
                except Exception as e:
                    st.error(f"❌ Error searching businesses: {e}")
                    import traceback
                    st.code(traceback.format_exc())
                    st.info("💡 OSM services may be temporarily unavailable. Please try again in a moment.")
    
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
                {biz.get('address', 'No address')}<br>
                {f"Phone: {biz.get('phone', '')}" if biz.get('phone') else ''}
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

# Footer info
st.sidebar.markdown("---")
st.sidebar.markdown("### About This Version")
st.sidebar.info("""
**OpenStreetMap Version**
- ✅ 100% Free
- ✅ No API Key Required
- ✅ Open Source Data
- ⚠️ Website data may be incomplete
- ⚠️ No ratings/reviews
""")

