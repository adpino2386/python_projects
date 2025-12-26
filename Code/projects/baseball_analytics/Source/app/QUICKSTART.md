# Quick Start Guide

## Setup Instructions

### 1. Install Dependencies

```bash
cd Code/projects/baseball_analytics/Source/app
pip install -r requirements.txt
```

### 2. Configure Environment Variables

Create or update `Code/projects/baseball_analytics/Source/utils/.env`:

```env
# Database Configuration
DB_USER=your_postgres_user
DB_PASS=your_postgres_password
DB_HOST=localhost
DB_NAME=your_database_name

# Stripe Configuration (for payments)
STRIPE_PUBLISHABLE_KEY=pk_test_your_publishable_key
STRIPE_SECRET_KEY=sk_test_your_secret_key
```

### 3. Run the Application

**Windows:**
```bash
cd Code/projects/baseball_analytics/Source/app
streamlit run main.py
```

**Linux/Mac:**
```bash
cd Code/projects/baseball_analytics/Source/app
chmod +x run_app.sh
./run_app.sh
```

Or directly:
```bash
streamlit run main.py
```

### 4. Access the App

The app will open in your browser at `http://localhost:8501`

## MVP Features

### Free Tier (No Login Required)
- ✅ Dashboard with key metrics
- ✅ League standings
- ✅ Top players overview
- ✅ Grade distributions

### Premium Tier (Requires Payment/Login)
- 🎯 Game predictions with win probabilities
- 🔥 Best/worst matchup analysis
- ⚔️ Head-to-head player comparisons
- 🎲 Players due for hits (bad luck analysis)
- 📉 Players likely to cool off
- 📊 Advanced analytics and visualizations

## MVP Payment Flow

For MVP demo purposes:
1. Click "Login / Upgrade" in sidebar
2. Click "Get Premium Access (Demo)" button
3. Premium features are immediately unlocked

**For Production:**
- Integrate with Stripe Checkout
- Use Stripe webhooks to verify payments
- Store user subscriptions in database
- Implement proper authentication

## Testing

1. **Free Features**: All features work without login
2. **Premium Features**: Click "Get Premium Access (Demo)" to unlock
3. **Navigation**: Use sidebar to navigate between pages
4. **Data**: Make sure your database has:
   - `dim_pitcher_archetypes` table
   - `dim_hitter_archetypes` table
   - `fact_player_luck_summary` table (for luck analysis)
   - `dim_player` table

## Troubleshooting

### Database Connection Error
- Check your `.env` file has correct database credentials
- Ensure PostgreSQL is running
- Verify database name exists

### Import Errors
- Make sure you're running from the `app/` directory
- Check that all dependencies are installed
- Verify Python path includes the Source directory

### No Data Showing
- Run your ETL scripts to populate the database
- Check that tables exist and have data
- Verify table names match what the queries expect

## Next Steps for Production

1. **Stripe Integration**
   - Set up Stripe account and products
   - Implement proper checkout flow
   - Add webhook handlers for payment verification

2. **User Management**
   - Implement user registration/login
   - Store user data in database
   - Add password hashing and session management

3. **Data Integration**
   - Integrate with MLB Stats API for live games
   - Add daily schedule updates
   - Implement real-time score updates

4. **Performance**
   - Add Redis caching for frequently accessed data
   - Optimize database queries
   - Implement pagination for large datasets

5. **Deployment**
   - Deploy to Streamlit Cloud, Heroku, or AWS
   - Set up CI/CD pipeline
   - Add monitoring and logging

