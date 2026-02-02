# RadarLead - Business Lead Finder

A web application that helps you find businesses without websites using Google Places API. Perfect for agencies looking to help businesses establish their online presence.

## Features

- 🔍 **Text-based Search**: Search by business type and location (e.g., "Plumbers in Montreal")
- 🗺️ **Coordinate-based Search**: Search by latitude/longitude with custom radius
- 📊 **Database Storage**: All searches and results are stored for future reference
- 📥 **Export Functionality**: Export results as CSV or JSON
- 🎨 **User-friendly Interface**: Clean, modern UI for non-technical users

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following variables:

```env
# Google Places API Key (Required)
GOOGLE_PLACES_API_KEY=your_api_key_here

# PostgreSQL Database Configuration (Required)
DB_USER=your_db_username
DB_PASS=your_db_password
DB_HOST=localhost
DB_NAME=radarlead

# Flask Secret Key (for production)
SECRET_KEY=your-secret-key-here
```

**To get Google Places API Key:**
1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create a new project or select an existing one
3. Enable the "Places API" and "Geocoding API"
4. Create credentials (API Key)
5. Add it to your `.env` file

**PostgreSQL Setup:**
1. Make sure PostgreSQL is installed and running
2. Create a database: `CREATE DATABASE radarlead;`
3. Update the `.env` file with your database credentials

### 3. Run the Application

**Option 1: Streamlit (Recommended - Simpler & More User-Friendly)**

```bash
streamlit run streamlit_app.py
```

The app will automatically open in your browser at `http://localhost:8501`

**Option 2: Flask (If you prefer Flask)**

```bash
python app.py
```

The app will be available at `http://localhost:5000`

**Note:** Streamlit is recommended as it's simpler, has a better UI out of the box, and avoids Flask-SQLAlchemy connection issues.

## Usage

### Text-based Search
1. Select "Search by Location"
2. Enter business type (e.g., "Plumbers", "Hotels")
3. Enter location (e.g., "Montreal, Quebec, Canada")
4. Click "Search Businesses"

### Coordinate-based Search
1. Select "Search by Coordinates"
2. Enter business type
3. Enter latitude and longitude
4. (Optional) Set search radius in meters (default: 10km)
5. Click "Search Businesses"

## Database

The application uses **PostgreSQL** for data storage. The database connection is configured via the `.env` file using the `DB_USER`, `DB_PASS`, `DB_HOST`, and `DB_NAME` variables.

**Note:** If PostgreSQL connection fails, the app will fall back to SQLite for development purposes.

Database models:
- **SearchQuery**: Stores search parameters and metadata
- **Business**: Stores individual business information

The database tables will be automatically created on first run.

## API Endpoints

- `POST /api/search` - Search for businesses
- `GET /api/searches` - Get all past searches
- `GET /api/search/<id>/businesses` - Get businesses for a specific search

## Environment Variables

All environment variables are loaded from the `.env` file:

- `GOOGLE_PLACES_API_KEY` - Your Google Places API key (required)
- `DB_USER` - PostgreSQL username (required)
- `DB_PASS` - PostgreSQL password (required)
- `DB_HOST` - PostgreSQL host (default: localhost)
- `DB_NAME` - PostgreSQL database name (required)
- `SECRET_KEY` - Flask secret key (for production)

## Notes

- Google Places API has usage limits and costs. Check [Google's pricing](https://developers.google.com/maps/billing-and-pricing/pricing)
- The free tier includes $200/month credit
- Consider implementing rate limiting for production use
- For production, use a proper database (PostgreSQL recommended)

## License

MIT

