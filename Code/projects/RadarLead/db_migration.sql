-- RadarLead DB Migration
-- Run this once against your PostgreSQL database to add AI enrichment support.
-- Safe to run multiple times (uses IF NOT EXISTS / DO NOTHING patterns).

-- 1. Add AI enrichment columns to businesses table
ALTER TABLE businesses
    ADD COLUMN IF NOT EXISTS website_pitch       TEXT,
    ADD COLUMN IF NOT EXISTS decision_maker_title VARCHAR(100),
    ADD COLUMN IF NOT EXISTS personalized_opener  TEXT,
    ADD COLUMN IF NOT EXISTS lead_score           INTEGER,
    ADD COLUMN IF NOT EXISTS niche_tag            VARCHAR(100),
    ADD COLUMN IF NOT EXISTS pain_points          TEXT,   -- JSON array stored as string
    ADD COLUMN IF NOT EXISTS is_enriched          BOOLEAN DEFAULT FALSE,
    ADD COLUMN IF NOT EXISTS enrichment_error     TEXT,
    ADD COLUMN IF NOT EXISTS enriched_at          TIMESTAMP;

-- 2. Users table (for SaaS auth + credit tracking)
CREATE TABLE IF NOT EXISTS users (
    id                  SERIAL PRIMARY KEY,
    email               VARCHAR(255) UNIQUE NOT NULL,
    password_hash       VARCHAR(255),                    -- set when you add auth
    plan                VARCHAR(50)  DEFAULT 'free',
    credits             INTEGER      DEFAULT 10,         -- 10 free credits on signup
    stripe_customer_id  VARCHAR(100),
    created_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

-- 3. Credit usage log (optional but useful for billing disputes / analytics)
CREATE TABLE IF NOT EXISTS credit_usage (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER REFERENCES users(id) ON DELETE CASCADE,
    action      VARCHAR(100) NOT NULL,  -- e.g. 'enrich_lead'
    credits_used INTEGER DEFAULT 1,
    business_id INTEGER REFERENCES businesses(id) ON DELETE SET NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 4. Index for fast enrichment status lookups
CREATE INDEX IF NOT EXISTS idx_businesses_is_enriched
    ON businesses(is_enriched);

CREATE INDEX IF NOT EXISTS idx_businesses_lead_score
    ON businesses(lead_score DESC);

CREATE INDEX IF NOT EXISTS idx_businesses_niche_tag
    ON businesses(niche_tag);
