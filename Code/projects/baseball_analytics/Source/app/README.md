# Baseball Analytics MVP - Streamlit Web App

A modern web application for baseball analytics with premium features and Stripe payment integration.

## Features

### Free Tier
- Dashboard overview
- League standings
- Basic player statistics
- Team information

### Premium Tier (Requires Payment)
- Game predictions with win probabilities
- Best/worst matchup analysis
- Head-to-head player comparisons
- Players due for hits (bad luck analysis)
- Players likely to cool off (regression analysis)
- Advanced analytics and visualizations
- Historical matchup data
- Game simulations

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up environment variables in `utils/.env`:
```
DB_USER=your_db_user
DB_PASS=your_db_password
DB_HOST=your_db_host
DB_NAME=your_db_name
STRIPE_PUBLISHABLE_KEY=pk_test_your_key
STRIPE_SECRET_KEY=sk_test_your_key
```

3. Run the app:
```bash
streamlit run main.py
```

## Stripe Setup

1. Create a Stripe account at https://stripe.com
2. Get your API keys from the Stripe dashboard
3. Create a product and price in Stripe dashboard
4. Update the price ID in `utils/stripe_helper.py`

## Project Structure

```
app/
├── main.py                 # Main entry point
├── pages/                  # Page modules
│   ├── home.py            # Home page (free)
│   ├── dashboard.py       # Dashboard (free)
│   ├── predictions.py     # Predictions (premium)
│   ├── comparisons.py     # Comparisons (premium)
│   ├── standings.py       # Standings (free)
│   └── payment.py         # Payment/login
├── utils/                  # Utilities
│   ├── app_helpers.py     # App helper functions
│   └── stripe_helper.py   # Stripe integration
└── requirements.txt        # Python dependencies
```

## MVP Notes

- For MVP demo, payment is simplified - clicking "Get Premium Access" grants access
- In production, implement proper Stripe Checkout with webhooks
- Database queries are cached for 5 minutes to improve performance
- Some features use sample data - integrate with MLB API for production

## Future Enhancements

- Real-time game tracking
- Email notifications
- Mobile app
- Advanced filtering and search
- Export functionality
- API access for premium users

