"""
RadarLead UI Pages
Reusable Streamlit page renderers: auth (login/signup) and pricing/upgrade.
Import and call from streamlit_app.py.
"""
import streamlit as st
from services.billing_service import PLANS


# ═════════════════════════════════════════════════════════════════════════════
# Auth page
# ═════════════════════════════════════════════════════════════════════════════

def render_auth_page(auth_service) -> bool:
    """
    Render the login / signup page.
    Sets st.session_state.user on success.

    Returns:
        True if the user is now logged in, False otherwise.
    """
    st.title("🔍 RadarLead")
    st.markdown("#### Find businesses without websites — enrich with AI outreach intelligence")
    st.divider()

    tab_login, tab_signup = st.tabs(["Log in", "Create account"])

    # ── Log in ────────────────────────────────────────────────────────────────
    with tab_login:
        st.markdown("##### Welcome back")
        email_in = st.text_input("Email", key="login_email", placeholder="you@example.com")
        pass_in  = st.text_input("Password", type="password", key="login_pass")

        if st.button("Log in", type="primary", use_container_width=True, key="btn_login"):
            if not email_in or not pass_in:
                st.error("Please enter your email and password.")
            else:
                result = auth_service.login(email_in, pass_in)
                if result["ok"]:
                    st.session_state.user = result["user"]
                    st.success(f"Welcome back, {result['user']['email']} 👋")
                    st.rerun()
                else:
                    st.error(result["error"])

    # ── Sign up ───────────────────────────────────────────────────────────────
    with tab_signup:
        st.markdown("##### Create your free account")
        st.caption("10 free AI enrichment credits on signup. No credit card required.")

        su_email = st.text_input("Email", key="su_email", placeholder="you@example.com")
        su_pass  = st.text_input("Password (min 8 chars)", type="password", key="su_pass")
        su_pass2 = st.text_input("Confirm password", type="password", key="su_pass2")

        if st.button("Create account", type="primary", use_container_width=True, key="btn_signup"):
            if not su_email or not su_pass:
                st.error("Email and password are required.")
            elif su_pass != su_pass2:
                st.error("Passwords don't match.")
            elif len(su_pass) < 8:
                st.error("Password must be at least 8 characters.")
            else:
                result = auth_service.signup(su_email, su_pass)
                if result["ok"]:
                    st.session_state.user = result["user"]
                    st.success("Account created! You have 10 free enrichment credits.")
                    st.rerun()
                else:
                    st.error(result["error"])

    return "user" in st.session_state


# ═════════════════════════════════════════════════════════════════════════════
# Pricing / upgrade page
# ═════════════════════════════════════════════════════════════════════════════

PLAN_FEATURES = {
    "starter": [
        "100 AI-enriched leads / month",
        "Lead score (1–10)",
        "Niche tag + contact title",
        "Personalized email opener",
        "Pain points analysis",
        "CSV / JSON export",
    ],
    "agency": [
        "500 AI-enriched leads / month",
        "Everything in Starter",
        "Priority enrichment queue",
        "Batch export up to 500 rows",
        "Email support",
    ],
    "pro": [
        "2,000 AI-enriched leads / month",
        "Everything in Agency",
        "REST API access",
        "Webhook integration (Zapier / Make)",
        "Dedicated onboarding call",
    ],
}


def render_pricing_page(user: dict, billing_service=None):
    """
    Render the upgrade / pricing page.
    Shows current plan and Stripe checkout links for higher tiers.
    """
    st.title("💳 Plans & Pricing")
    current_plan = user.get("plan", "free")
    credits_left  = user.get("credits", 0)

    # Current status banner
    st.info(
        f"You are on the **{current_plan.capitalize()}** plan "
        f"with **{credits_left} enrichment credit{'s' if credits_left != 1 else ''}** remaining.",
        icon="ℹ️",
    )

    if current_plan == "free":
        st.markdown(
            "Upgrade to unlock more AI enrichment credits each month. "
            "You'll be redirected to Stripe — cancel anytime."
        )

    st.divider()

    cols = st.columns(3)
    plan_keys = ["starter", "agency", "pro"]
    highlighted = "agency"  # most popular

    for col, key in zip(cols, plan_keys):
        plan = PLANS[key]
        features = PLAN_FEATURES[key]
        is_current = current_plan == key
        is_popular = key == highlighted

        with col:
            if is_popular:
                st.markdown(
                    "<div style='text-align:center;font-size:12px;font-weight:500;"
                    "color:var(--color-text-info);margin-bottom:4px'>Most popular</div>",
                    unsafe_allow_html=True,
                )

            border_style = (
                "border:2px solid var(--color-border-info);border-radius:12px;padding:20px;"
                if is_popular
                else "border:0.5px solid var(--color-border-tertiary);border-radius:12px;padding:20px;"
            )

            with st.container():
                st.markdown(f"<div style='{border_style}'>", unsafe_allow_html=True)
                st.markdown(f"### {plan['name']}")
                st.markdown(f"**${plan['price_monthly']}** / month")
                st.markdown(f"_{plan['description']}_")
                st.markdown("---")
                for feat in features:
                    st.markdown(f"✓ {feat}")
                st.markdown("</div>", unsafe_allow_html=True)

            st.write("")  # spacing

            if is_current:
                st.button(
                    "Current plan", key=f"plan_{key}",
                    disabled=True, use_container_width=True,
                )
            else:
                label = "Upgrade" if _plan_rank(key) > _plan_rank(current_plan) else "Switch"
                if st.button(
                    f"{label} to {plan['name']}",
                    key=f"plan_{key}",
                    type="primary" if is_popular else "secondary",
                    use_container_width=True,
                ):
                    if billing_service is None:
                        st.warning(
                            "Stripe is not configured yet. "
                            "Add STRIPE_SECRET_KEY to your .env to enable payments.",
                            icon="⚠️",
                        )
                    else:
                        try:
                            url = billing_service.create_checkout_session(
                                plan_key=key,
                                user_email=user["email"],
                                success_url="http://localhost:8501",
                                cancel_url="http://localhost:8501",
                            )
                            st.markdown(
                                f'<meta http-equiv="refresh" content="0; url={url}">',
                                unsafe_allow_html=True,
                            )
                            st.info(f"Redirecting to Stripe checkout… [click here if not redirected]({url})")
                        except Exception as e:
                            st.error(f"Could not create checkout session: {e}")

    st.divider()
    st.caption(
        "All plans include a 7-day free trial. "
        "You will not be charged until the trial ends. Cancel anytime from your Stripe dashboard."
    )


def _plan_rank(plan: str) -> int:
    return {"free": 0, "starter": 1, "agency": 2, "pro": 3}.get(plan, 0)
