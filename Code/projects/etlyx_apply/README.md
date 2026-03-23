# Etlyx Apply — AI Job Hunt Assistant

Multi-agent job search with free/pro tiers, Supabase auth, and Stripe payments.

---

## Phase status
- [x] Phase 1 — Auth (Supabase login, signup, session, free/pro gating)
- [x] Phase 2 — Stripe payments (checkout, webhooks, portal, cancellation)
- [ ] Phase 3 — Deploy to Railway/Render (public URL)

---

## First-time setup (do this once)

### 1. Install Node.js
Download from **https://nodejs.org** → choose LTS.

### 2. Run the Supabase schema (if you haven't already)
1. Go to **https://supabase.com** → your project → SQL Editor → New query
2. Open `supabase-schema.sql`, copy it all, paste it in, click Run

### 3. Set up Stripe

**a) Create a Stripe account**
Go to **https://stripe.com** → sign up (it's free)

**b) Get your API keys**
Stripe Dashboard → Developers → API keys
- Copy the **Secret key** (starts with `sk_test_...`)

**c) Create your $15/month product**
1. Stripe Dashboard → Products → Add product
2. Name: "Etlyx Apply Pro"
3. Pricing: $15.00 · Recurring · Monthly
4. Click Save product
5. Copy the **Price ID** (starts with `price_...`)

**d) Set up the webhook (for local testing)**
Install the Stripe CLI: **https://stripe.com/docs/stripe-cli**
```bash
stripe login
stripe listen --forward-to localhost:3001/api/stripe/webhook
```
Copy the **webhook signing secret** it prints (starts with `whsec_...`)

**e) Enable the Customer Portal**
Stripe Dashboard → Settings → Billing → Customer portal → Activate

### 4. Fill in your .env

Open the `.env` file in VS Code and fill in every value:
```
ANTHROPIC_API_KEY=sk-ant-...
SUPABASE_URL=https://fahqfugnqldwueapcdnm.supabase.co
SUPABASE_SERVICE_ROLE_KEY=...your rotated service role key...
VITE_SUPABASE_URL=https://fahqfugnqldwueapcdnm.supabase.co
VITE_SUPABASE_ANON_KEY=eyJhbGci...
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID=price_...
FRONTEND_URL=http://localhost:5173
```

### 5. Install dependencies
```bash
npm install
```

---

## Running the app

**Terminal 1** — start the app:
```bash
npm run dev
```

**Terminal 2** — start the Stripe webhook listener (needed for payments to work locally):
```bash
stripe listen --forward-to localhost:3001/api/stripe/webhook
```

Open **http://localhost:5173**

---

## How the payment flow works

```
User clicks "Upgrade" 
  → Frontend calls POST /api/stripe/checkout
  → Server creates Stripe Checkout Session
  → User is redirected to stripe.com to pay
  → After payment, Stripe redirects to /success
  → Stripe also sends a webhook to POST /api/stripe/webhook
  → Server receives "checkout.session.completed" event
  → Server updates profiles.plan = 'pro' in Supabase
  → User's plan badge updates to "Pro" in the topbar
```

## Test card for Stripe
Use card number `4242 4242 4242 4242`, any future expiry, any CVC.

---

## Free vs Pro

| Feature | Free | Pro ($15/mo) |
|---|---|---|
| Job search | Indeed only | LinkedIn + Indeed + hiring.cafe + Banks |
| Searches/month | 5 | Unlimited |
| Evaluator Agent | ✗ | ✓ Full breakdown |
| Cover letters | ✗ | ✓ Unlimited |
| Tracker | ✓ | ✓ |

To manually upgrade a user for testing (without Stripe):
Supabase → Table Editor → profiles → find user row → change `plan` to `pro` → Save

---

## Project structure

```
etlyx-apply/
├── server.js                 ← Auth, usage limits, AI proxy, Stripe endpoints + webhook
├── vite.config.js
├── index.html
├── package.json
├── supabase-schema.sql       ← Run once in Supabase SQL Editor
├── .env                      ← All your secrets
└── src/
    ├── main.jsx              ← React entry + AuthProvider
    ├── App.jsx               ← Main app + routing (app/pricing/success/account)
    ├── lib/
    │   ├── supabase.js       ← Supabase client
    │   └── auth.js           ← Auth context (user, plan, isPro)
    ├── pages/
    │   ├── Login.jsx         ← Sign up / log in
    │   ├── Pricing.jsx       ← Free vs Pro + Stripe checkout trigger
    │   ├── Success.jsx       ← Post-payment confirmation page
    │   └── Account.jsx       ← Plan status + Stripe portal + sign out
    └── components/
        └── UpgradeWall.jsx   ← Locked feature screen
```

---

## Next step: Phase 3 — Deploy to the world

Once you're happy with local testing, Phase 3 covers:
- Deploying backend + frontend to Railway (one platform, simple)
- Setting up a production Stripe webhook with the real URL
- Pointing your domain (etlyx.io or etlyx.com) at it
- Switching Stripe from test mode to live mode
