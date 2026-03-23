"""
Auth Service - RadarLead
Handles user signup, login, password hashing, and session helpers.
Uses PostgreSQL — no extra dependencies beyond what's already in requirements.txt.
"""
import hashlib
import hmac
import os
import secrets
from datetime import datetime
from typing import Optional
from sqlalchemy import text


# ── Helpers ───────────────────────────────────────────────────────────────────

def _hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Return (hash, salt) for a password. Pass existing salt to verify."""
    if salt is None:
        salt = secrets.token_hex(16)
    digest = hmac.new(
        salt.encode(), password.encode(), hashlib.sha256
    ).hexdigest()
    return digest, salt


def _verify_password(password: str, stored_hash: str, salt: str) -> bool:
    computed, _ = _hash_password(password, salt)
    return hmac.compare_digest(computed, stored_hash)


# ── AuthService ───────────────────────────────────────────────────────────────

class AuthService:
    """User signup, login and lookup against the users table."""

    FREE_CREDITS = 10  # credits granted on signup

    def __init__(self, engine):
        self.engine = engine
        self._ensure_table()

    # ── Schema ────────────────────────────────────────────────────────────────

    def _ensure_table(self):
        """Create users table if it doesn't exist."""
        with self.engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id                 SERIAL PRIMARY KEY,
                    email              VARCHAR(255) UNIQUE NOT NULL,
                    password_hash      VARCHAR(255) NOT NULL,
                    password_salt      VARCHAR(64)  NOT NULL,
                    plan               VARCHAR(50)  DEFAULT 'free',
                    credits            INTEGER      DEFAULT 10,
                    stripe_customer_id VARCHAR(100),
                    created_at         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP,
                    updated_at         TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
                )
            """))
            # Safe migration: add password_salt if missing (older schemas)
            try:
                conn.execute(text(
                    "ALTER TABLE users ADD COLUMN IF NOT EXISTS password_salt VARCHAR(64) NOT NULL DEFAULT ''"
                ))
            except Exception:
                pass
            conn.commit()

    # ── Public API ────────────────────────────────────────────────────────────

    def signup(self, email: str, password: str) -> dict:
        """
        Create a new user.

        Returns:
            {'ok': True, 'user': {...}} or {'ok': False, 'error': '...'}
        """
        email = email.strip().lower()
        if not email or "@" not in email:
            return {"ok": False, "error": "Invalid email address."}
        if len(password) < 8:
            return {"ok": False, "error": "Password must be at least 8 characters."}

        pw_hash, salt = _hash_password(password)

        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    INSERT INTO users (email, password_hash, password_salt, plan, credits)
                    VALUES (:email, :pw_hash, :salt, 'free', :credits)
                    RETURNING id, email, plan, credits, created_at
                """), {
                    "email": email,
                    "pw_hash": pw_hash,
                    "salt": salt,
                    "credits": self.FREE_CREDITS,
                })
                row = result.fetchone()
                conn.commit()
                return {"ok": True, "user": _row_to_dict(row)}
        except Exception as e:
            if "duplicate key" in str(e).lower() or "unique" in str(e).lower():
                return {"ok": False, "error": "An account with this email already exists."}
            return {"ok": False, "error": f"Signup failed: {e}"}

    def login(self, email: str, password: str) -> dict:
        """
        Verify credentials.

        Returns:
            {'ok': True, 'user': {...}} or {'ok': False, 'error': '...'}
        """
        email = email.strip().lower()
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, email, password_hash, password_salt, plan, credits, stripe_customer_id, created_at
                    FROM users WHERE email = :email
                """), {"email": email})
                row = result.fetchone()

            if row is None:
                return {"ok": False, "error": "No account found with that email."}

            row_dict = dict(row._mapping)
            if not _verify_password(password, row_dict["password_hash"], row_dict["password_salt"]):
                return {"ok": False, "error": "Incorrect password."}

            user = {k: v for k, v in row_dict.items()
                    if k not in ("password_hash", "password_salt")}
            return {"ok": True, "user": user}

        except Exception as e:
            return {"ok": False, "error": f"Login failed: {e}"}

    def get_user(self, user_id: int) -> Optional[dict]:
        """Fetch a user by ID. Returns None if not found."""
        try:
            with self.engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT id, email, plan, credits, stripe_customer_id, created_at
                    FROM users WHERE id = :id
                """), {"id": user_id})
                row = result.fetchone()
            return dict(row._mapping) if row else None
        except Exception:
            return None

    def deduct_credits(self, user_id: int, amount: int = 1) -> dict:
        """
        Deduct credits from a user. Returns the new credit balance.

        Returns:
            {'ok': True, 'credits_remaining': N} or {'ok': False, 'error': '...'}
        """
        try:
            with self.engine.connect() as conn:
                # Check current balance first
                result = conn.execute(text(
                    "SELECT credits FROM users WHERE id = :id FOR UPDATE"
                ), {"id": user_id})
                row = result.fetchone()
                if row is None:
                    return {"ok": False, "error": "User not found."}

                current = row[0]
                if current < amount:
                    return {
                        "ok": False,
                        "error": f"Not enough credits. You have {current}, need {amount}.",
                        "credits_remaining": current,
                    }

                conn.execute(text("""
                    UPDATE users
                    SET credits = credits - :amount, updated_at = NOW()
                    WHERE id = :id
                """), {"amount": amount, "id": user_id})
                conn.commit()
                return {"ok": True, "credits_remaining": current - amount}
        except Exception as e:
            return {"ok": False, "error": str(e)}

    def add_credits(self, user_id: int, amount: int, plan: str) -> bool:
        """Grant credits and update plan (called after Stripe webhook)."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE users
                    SET credits = credits + :amount, plan = :plan, updated_at = NOW()
                    WHERE id = :id
                """), {"amount": amount, "plan": plan, "id": user_id})
                conn.commit()
            return True
        except Exception:
            return False

    def add_credits_by_email(self, email: str, amount: int, plan: str,
                             stripe_customer_id: str = "") -> bool:
        """Grant credits by email — used in Stripe webhook handler."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    UPDATE users
                    SET credits = credits + :amount,
                        plan = :plan,
                        stripe_customer_id = COALESCE(NULLIF(:scid, ''), stripe_customer_id),
                        updated_at = NOW()
                    WHERE email = :email
                """), {
                    "amount": amount, "plan": plan,
                    "scid": stripe_customer_id, "email": email,
                })
                conn.commit()
            return True
        except Exception:
            return False

    def log_credit_usage(self, user_id: int, action: str, business_id: Optional[int] = None):
        """Write a row to credit_usage for audit trail (best-effort)."""
        try:
            with self.engine.connect() as conn:
                conn.execute(text("""
                    CREATE TABLE IF NOT EXISTS credit_usage (
                        id           SERIAL PRIMARY KEY,
                        user_id      INTEGER REFERENCES users(id) ON DELETE CASCADE,
                        action       VARCHAR(100) NOT NULL,
                        credits_used INTEGER DEFAULT 1,
                        business_id  INTEGER,
                        created_at   TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """))
                conn.execute(text("""
                    INSERT INTO credit_usage (user_id, action, business_id)
                    VALUES (:uid, :action, :bid)
                """), {"uid": user_id, "action": action, "bid": business_id})
                conn.commit()
        except Exception:
            pass  # never let audit logging crash the app


# ── Utilities ─────────────────────────────────────────────────────────────────

def _row_to_dict(row) -> dict:
    return {k: v for k, v in row._mapping.items()
            if k not in ("password_hash", "password_salt")}
