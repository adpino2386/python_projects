"""
Billing Service - RadarLead SaaS
Handles Stripe subscriptions, credit tracking, and plan management.
"""
import os
import stripe
from dotenv import load_dotenv

load_dotenv()

stripe.api_key = os.getenv("STRIPE_SECRET_KEY", "")

# Plan definitions — update price IDs after creating products in Stripe dashboard
PLANS = {
    "starter": {
        "name": "Starter",
        "price_id": os.getenv("STRIPE_PRICE_STARTER", "price_starter_placeholder"),
        "price_monthly": 49,
        "credits": 100,
        "description": "100 AI-enriched leads/month",
    },
    "agency": {
        "name": "Agency",
        "price_id": os.getenv("STRIPE_PRICE_AGENCY", "price_agency_placeholder"),
        "price_monthly": 149,
        "credits": 500,
        "description": "500 AI-enriched leads/month",
    },
    "pro": {
        "name": "Pro",
        "price_id": os.getenv("STRIPE_PRICE_PRO", "price_pro_placeholder"),
        "price_monthly": 399,
        "credits": 2000,
        "description": "2,000 AI-enriched leads/month + API access",
    },
}


class BillingService:
    """Manages Stripe checkout sessions and subscription webhooks."""

    def create_checkout_session(
        self, plan_key: str, user_email: str, success_url: str, cancel_url: str
    ) -> str:
        """
        Create a Stripe Checkout Session for a subscription plan.

        Returns:
            Checkout URL to redirect the user to.
        """
        if not stripe.api_key or stripe.api_key == "":
            raise ValueError("STRIPE_SECRET_KEY not configured in .env")

        plan = PLANS.get(plan_key)
        if not plan:
            raise ValueError(f"Unknown plan: {plan_key}")

        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            mode="subscription",
            customer_email=user_email,
            line_items=[{"price": plan["price_id"], "quantity": 1}],
            success_url=success_url + "?session_id={CHECKOUT_SESSION_ID}",
            cancel_url=cancel_url,
            metadata={"plan": plan_key},
        )
        return session.url

    def handle_webhook(self, payload: bytes, sig_header: str) -> dict:
        """
        Process a Stripe webhook event.

        Returns:
            dict with 'event_type', 'user_email', 'plan', 'credits' on
            checkout.session.completed — or {'event_type': other} otherwise.
        """
        secret = os.getenv("STRIPE_WEBHOOK_SECRET", "")
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, secret)
        except stripe.error.SignatureVerificationError:
            raise ValueError("Invalid webhook signature")

        if event["type"] == "checkout.session.completed":
            obj = event["data"]["object"]
            plan_key = obj.get("metadata", {}).get("plan", "starter")
            plan = PLANS.get(plan_key, PLANS["starter"])
            return {
                "event_type": "checkout.session.completed",
                "user_email": obj.get("customer_email", ""),
                "stripe_customer_id": obj.get("customer", ""),
                "plan": plan_key,
                "credits": plan["credits"],
            }

        if event["type"] in (
            "customer.subscription.deleted",
            "customer.subscription.paused",
        ):
            obj = event["data"]["object"]
            return {
                "event_type": event["type"],
                "stripe_customer_id": obj.get("customer", ""),
            }

        return {"event_type": event["type"]}
