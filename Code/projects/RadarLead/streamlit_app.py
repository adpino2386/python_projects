"""
RadarLead — main Streamlit entry point.
Handles auth gating, navigation, search, AI enrichment, and pricing.
"""
import streamlit as st
import pandas as pd
from datetime import datetime
import os
import json
from dotenv import load_dotenv
from sqlalchemy import text

from services.places_service import PlacesService
from services.enrichment_service import EnrichmentService
from services.auth_service import AuthService
from services.billing_service import BillingService, PLANS
from utils.connection_engine import create_connection_postgresql
from pages_ui import render_auth_page, render_pricing_page

import folium
from streamlit_folium import st_folium

load_dotenv()

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="RadarLead",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Init core services ────────────────────────────────────────────────────────
if "db_engine" not in st.session_state:
    try:
        st.session_state.db_engine = create_connection_postgresql()
    except Exception as e:
        st.warning(f"⚠️ Could not connect to PostgreSQL: {e}")
        st.session_state.db_engine = None

if "auth_service" not in st.session_state:
    if st.session_state.db_engine:
        st.session_state.auth_service = AuthService(st.session_state.db_engine)
    else:
        st.session_state.auth_service = None

if "places_service" not in st.session_state:
    try:
        st.session_state.places_service = PlacesService()
    except ValueError:
        st.session_state.places_service = None

if "enrichment_service" not in st.session_state:
    try:
        st.session_state.enrichment_service = EnrichmentService()
    except ValueError:
        st.session_state.enrichment_service = None

if "billing_service" not in st.session_state:
    try:
        st.session_state.billing_service = BillingService()
    except Exception:
        st.session_state.billing_service = None

# ── Auth gate ─────────────────────────────────────────────────────────────────
if "user" not in st.session_state:
    if st.session_state.auth_service is None:
        st.error("Database not connected — cannot authenticate users.")
        st.stop()
    if not render_auth_page(st.session_state.auth_service):
        st.stop()

# ── User is logged in from here ───────────────────────────────────────────────
user = st.session_state.user

# Refresh credit balance from DB on each load
if st.session_state.db_engine:
    fresh = st.session_state.auth_service.get_user(user["id"])
    if fresh:
        st.session_state.user = fresh
        user = fresh

# ── DB table init ─────────────────────────────────────────────────────────────
if st.session_state.db_engine:
    try:
        with st.session_state.db_engine.connect() as conn:
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS search_queries (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
                    business_type VARCHAR(200) NOT NULL,
                    location VARCHAR(500) NOT NULL,
                    search_type VARCHAR(50) NOT NULL,
                    latitude FLOAT, longitude FLOAT, radius INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    results_count INTEGER DEFAULT 0,
                    businesses_without_website INTEGER DEFAULT 0
                )
            """))
            # Add user_id column to existing search_queries tables
            try:
                conn.execute(text(
                    "ALTER TABLE search_queries ADD COLUMN IF NOT EXISTS "
                    "user_id INTEGER REFERENCES users(id) ON DELETE SET NULL"
                ))
            except Exception:
                pass
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS businesses (
                    id SERIAL PRIMARY KEY,
                    search_query_id INTEGER REFERENCES search_queries(id) ON DELETE CASCADE,
                    place_id VARCHAR(200) UNIQUE NOT NULL,
                    name VARCHAR(500) NOT NULL,
                    address TEXT, phone VARCHAR(50),
                    website VARCHAR(500), has_website BOOLEAN DEFAULT FALSE,
                    rating FLOAT, total_ratings INTEGER DEFAULT 0,
                    latitude FLOAT, longitude FLOAT,
                    business_status VARCHAR(50), price_level INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    website_pitch TEXT, decision_maker_title VARCHAR(100),
                    personalized_opener TEXT, lead_score INTEGER,
                    niche_tag VARCHAR(100), pain_points TEXT,
                    is_enriched BOOLEAN DEFAULT FALSE,
                    enrichment_error TEXT, enriched_at TIMESTAMP
                )
            """))
            for col_sql in [
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS price_level INTEGER",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS website_pitch TEXT",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS decision_maker_title VARCHAR(100)",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS personalized_opener TEXT",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS lead_score INTEGER",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS niche_tag VARCHAR(100)",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS pain_points TEXT",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS is_enriched BOOLEAN DEFAULT FALSE",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS enrichment_error TEXT",
                "ALTER TABLE businesses ADD COLUMN IF NOT EXISTS enriched_at TIMESTAMP",
            ]:
                try:
                    conn.execute(text(col_sql))
                except Exception:
                    pass
            conn.commit()
    except Exception as e:
        st.warning(f"⚠️ DB init error: {e}")

# ── Sidebar ───────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown(f"**{user['email']}**")
    plan_label = user.get("plan", "free").capitalize()
    credits    = user.get("credits", 0)
    st.caption(f"{plan_label} plan · {credits} credit{'s' if credits != 1 else ''} left")

    if credits == 0:
        st.warning("No credits remaining — upgrade to continue enriching leads.")
    elif credits <= 10:
        st.warning(f"⚡ Only {credits} credits left!")

    st.divider()
    page = st.selectbox(
        "Navigation",
        ["🔍 Search by Location", "🗺️ Search by Map", "💳 Plans & Pricing"],
        index=0,
    )
    st.divider()
    if st.button("Log out", use_container_width=True):
        for k in ("user", "businesses", "businesses_without_website",
                  "filter_option", "map_center", "search_location"):
            st.session_state.pop(k, None)
        st.rerun()


# ── DB helpers ────────────────────────────────────────────────────────────────

def save_businesses_to_db(conn, businesses, search_query_id):
    for biz in businesses:
        conn.execute(text("""
            INSERT INTO businesses
                (search_query_id, place_id, name, address, phone, website,
                 has_website, rating, total_ratings, latitude, longitude,
                 business_status, price_level)
            VALUES
                (:sqid, :pid, :name, :addr, :phone, :web,
                 :hw, :rating, :tr, :lat, :lng, :bs, :pl)
            ON CONFLICT (place_id) DO UPDATE SET
                rating = EXCLUDED.rating,
                total_ratings = EXCLUDED.total_ratings,
                price_level = EXCLUDED.price_level
        """), {
            "sqid": search_query_id,
            "pid":  biz.get("place_id", ""),
            "name": biz.get("name", ""),
            "addr": biz.get("address", ""),
            "phone":biz.get("phone", ""),
            "web":  biz.get("website", ""),
            "hw":   biz.get("has_website", False),
            "rating": biz.get("rating"),
            "tr":   biz.get("total_ratings", 0),
            "lat":  biz.get("latitude"),
            "lng":  biz.get("longitude"),
            "bs":   biz.get("business_status", ""),
            "pl":   biz.get("price_level"),
        })


def save_enrichment_to_db(conn, biz):
    if not biz.get("place_id"):
        return
    pain = biz.get("pain_points", [])
    conn.execute(text("""
        UPDATE businesses SET
            website_pitch = :wp, decision_maker_title = :dmt,
            personalized_opener = :po, lead_score = :ls,
            niche_tag = :nt, pain_points = :pp,
            is_enriched = :ie, enrichment_error = :ee, enriched_at = :ea
        WHERE place_id = :pid
    """), {
        "pid": biz.get("place_id"),
        "wp":  biz.get("website_pitch"),
        "dmt": biz.get("decision_maker_title"),
        "po":  biz.get("personalized_opener"),
        "ls":  biz.get("lead_score"),
        "nt":  biz.get("niche_tag"),
        "pp":  json.dumps(pain) if isinstance(pain, list) else pain,
        "ie":  biz.get("is_enriched", False),
        "ee":  biz.get("enrichment_error"),
        "ea":  datetime.utcnow() if biz.get("is_enriched") else None,
    })


def score_badge(score) -> str:
    if score is None: return ""
    s = int(score)
    if s >= 8: return "🔥"
    if s >= 5: return "⚡"
    return "❄️"


# ── display_results ───────────────────────────────────────────────────────────

def display_results(businesses, businesses_without_website):
    if not businesses:
        return

    if "filter_option" not in st.session_state:
        st.session_state.filter_option = "All Businesses"

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(businesses))
    c2.metric("Without Websites", len(businesses_without_website))
    c3.metric("With Websites", len(businesses) - len(businesses_without_website))
    avg = pd.DataFrame(businesses)["rating"].mean()
    c4.metric("Avg Rating", f"{avg:.1f}" if not pd.isna(avg) else "N/A")

    st.subheader("📋 Results")
    opts = ["All Businesses", "Without Websites Only", "With Websites Only"]
    idx  = opts.index(st.session_state.filter_option) if st.session_state.filter_option in opts else 0
    filt = st.radio("Show:", opts, horizontal=True, key="filter_option", index=idx)

    if filt == "All Businesses":
        disp = businesses
    elif filt == "Without Websites Only":
        disp = businesses_without_website
    else:
        disp = [b for b in businesses if b.get("has_website", False)]

    if not disp:
        st.info("ℹ️ No businesses match this filter.")
        return

    df = pd.DataFrame(disp)
    any_enriched = "is_enriched" in df.columns and df["is_enriched"].any()

    base = {
        "name": "Name", "address": "Address", "phone": "Phone",
        "website": "Website", "has_website": "Has Website",
        "rating": "Rating", "total_ratings": "Reviews",
        "price_level": "Price Level",
    }
    enrich = {
        "lead_score": "Score", "niche_tag": "Niche",
        "decision_maker_title": "Contact Title",
        "website_pitch": "Website Pitch",
        "personalized_opener": "Email Opener",
    }
    cols_map = {**base, **(enrich if any_enriched else {})}
    avail = [c for c in cols_map if c in df.columns]
    ddf   = df[avail].copy()
    ddf.columns = [cols_map[c] for c in avail]

    if "Rating" in ddf.columns:
        ddf["Rating"] = pd.to_numeric(ddf["Rating"], errors="coerce")
    if "Reviews" in ddf.columns:
        ddf["Reviews"] = pd.to_numeric(ddf["Reviews"], errors="coerce").fillna(0).astype(int)
    if "Price Level" in ddf.columns:
        pm = {0:"Free",1:"Inexpensive",2:"Moderate",3:"Expensive",4:"Very Expensive"}
        ddf["Price Level"] = ddf["Price Level"].map(pm).fillna("N/A")
    if "Has Website" in ddf.columns:
        ddf["Has Website"] = ddf["Has Website"].map({True: "Yes", False: "No"})
    if "Score" in ddf.columns:
        ddf["Score"] = ddf["Score"].apply(
            lambda x: f"{score_badge(x)} {int(x)}/10" if pd.notna(x) else ""
        )
    for col in ddf.columns:
        if ddf[col].dtype == "object":
            ddf[col] = ddf[col].fillna("")

    st.dataframe(ddf, use_container_width=True, hide_index=True)

    # Export
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    slug = filt.lower().replace(" ", "_")
    e1, e2 = st.columns(2)
    edf = pd.DataFrame(disp)
    with e1:
        st.download_button("📄 CSV", edf.to_csv(index=False),
                           file_name=f"radarlead_{slug}_{ts}.csv", mime="text/csv")
    with e2:
        st.download_button("📄 JSON", json.dumps(disp, indent=2, default=str),
                           file_name=f"radarlead_{slug}_{ts}.json", mime="application/json")


# ── render_enrich_section ─────────────────────────────────────────────────────

def render_enrich_section():
    biz_no_web = st.session_state.get("businesses_without_website", [])
    if not biz_no_web:
        return

    es = st.session_state.enrichment_service
    st.divider()
    st.subheader("🤖 AI Lead Enrichment")

    if es is None:
        st.warning("Add `ANTHROPIC_API_KEY` to your `.env` to enable AI enrichment.", icon="⚠️")
        return

    enriched_count = sum(1 for b in biz_no_web if b.get("is_enriched"))
    total     = len(biz_no_web)
    remaining = total - enriched_count

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Leads without website", total)
    c2.metric("Already enriched", enriched_count)
    c3.metric("To enrich", remaining)
    c4.metric("Your credits", user.get("credits", 0))

    if enriched_count == total:
        st.success("✅ All leads enriched — Score, Niche, and Email Opener columns are live above.")
        return

    # ── Credit gate ───────────────────────────────────────────────────────────
    credits_available = user.get("credits", 0)
    cost = remaining  # 1 credit per lead

    if credits_available == 0:
        st.error(
            "You have no enrichment credits left. "
            "Upgrade your plan to continue.",
        )
        if st.button("💳 View Plans & Pricing", use_container_width=True):
            st.session_state["_nav_override"] = "💳 Plans & Pricing"
            st.rerun()
        return

    can_enrich = min(remaining, credits_available)
    will_cost  = can_enrich

    if credits_available < remaining:
        st.warning(
            f"You have {credits_available} credit{'s' if credits_available != 1 else ''} "
            f"but need {remaining}. We'll enrich the first **{can_enrich}** leads.",
            icon="⚠️",
        )
    else:
        st.info(
            f"Enrich **{can_enrich} lead{'s' if can_enrich != 1 else ''}** "
            f"— costs **{will_cost} credit{'s' if will_cost != 1 else ''}**. "
            f"You'll have {credits_available - will_cost} left after.",
            icon="ℹ️",
        )

    if st.button(
        f"✨ Enrich {can_enrich} leads ({will_cost} credit{'s' if will_cost != 1 else ''})",
        type="primary", use_container_width=True,
    ):
        # Deduct credits first
        deduct = st.session_state.auth_service.deduct_credits(user["id"], will_cost)
        if not deduct["ok"]:
            st.error(deduct["error"])
            return

        # Update local user state immediately
        st.session_state.user["credits"] = deduct["credits_remaining"]

        progress_bar = st.progress(0, text="Starting enrichment…")
        status = st.empty()

        to_enrich = [b for b in biz_no_web if not b.get("is_enriched")][:can_enrich]

        def on_progress(done, total_):
            progress_bar.progress(done / total_, text=f"Enriched {done}/{total_}…")

        enriched_list = es.enrich_leads_batch(to_enrich, progress_callback=on_progress)
        enriched_map  = {e["place_id"]: e for e in enriched_list if e.get("place_id")}

        # Log credit usage
        for e_biz in enriched_list:
            st.session_state.auth_service.log_credit_usage(
                user["id"], "enrich_lead"
            )

        # Merge back into session state
        st.session_state.businesses_without_website = [
            {**b, **enriched_map.get(b.get("place_id", ""), {})} for b in biz_no_web
        ]
        st.session_state.businesses = [
            {**b, **enriched_map.get(b.get("place_id", ""), {})}
            for b in st.session_state.get("businesses", [])
        ]

        # Persist enrichment to DB
        if st.session_state.db_engine:
            try:
                with st.session_state.db_engine.connect() as conn:
                    for e_biz in enriched_list:
                        save_enrichment_to_db(conn, e_biz)
                    conn.commit()
                status.success("💾 Enrichment saved to database.")
            except Exception as ex:
                status.warning(f"⚠️ Could not save to DB: {ex}")

        progress_bar.progress(1.0, text="Done!")
        st.success(
            f"✅ Enriched {len(enriched_list)} leads! "
            f"{deduct['credits_remaining']} credit{'s' if deduct['credits_remaining'] != 1 else ''} remaining."
        )
        st.rerun()


# ── run_search ────────────────────────────────────────────────────────────────

def run_search(business_type, location_str, businesses, user_id):
    """Store search + businesses in DB, update session state."""
    businesses_without_website = (
        st.session_state.places_service.filter_businesses_without_website(businesses)
    )
    if st.session_state.db_engine:
        try:
            with st.session_state.db_engine.connect() as conn:
                r = conn.execute(text("""
                    INSERT INTO search_queries
                        (user_id, business_type, location, search_type,
                         results_count, businesses_without_website)
                    VALUES (:uid, :bt, :loc, 'text', :rc, :bww)
                    RETURNING id
                """), {
                    "uid": user_id, "bt": business_type, "loc": location_str,
                    "rc": len(businesses), "bww": len(businesses_without_website),
                })
                search_id = r.fetchone()[0]
                save_businesses_to_db(conn, businesses, search_id)
                conn.commit()
        except Exception as e:
            st.warning(f"⚠️ Could not save to database: {e}")

    st.session_state.businesses = businesses
    st.session_state.businesses_without_website = businesses_without_website
    st.session_state.filter_option = "All Businesses"
    return businesses_without_website


# ═════════════════════════════════════════════════════════════════════════════
# Navigation override (e.g. from "View Plans" button in enrichment section)
# ═════════════════════════════════════════════════════════════════════════════
nav_override = st.session_state.pop("_nav_override", None)
effective_page = nav_override if nav_override else page


# ═════════════════════════════════════════════════════════════════════════════
# Page: Search by Location
# ═════════════════════════════════════════════════════════════════════════════
if effective_page == "🔍 Search by Location":
    st.title("🔍 RadarLead")
    st.markdown("### Find businesses without websites, then enrich with AI outreach intelligence")

    if st.session_state.places_service is None:
        st.error("Google Places API key not configured. Add GOOGLE_PLACES_API_KEY to your .env.")
        st.stop()

    with st.sidebar:
        st.header("Search Options")
        search_type = st.radio("Search Type", ["📍 By Location", "🗺️ By Coordinates"])

    with st.form("search_form"):
        c1, c2 = st.columns(2)
        with c1:
            business_type = st.text_input("Business Type *", placeholder="Plumbers, Hotels, Restaurants…")
        if search_type == "📍 By Location":
            with c2:
                location = st.text_input("Location *", placeholder="Montreal, Quebec, Canada")
            latitude = longitude = radius = None
        else:
            with c2:
                cl, cg = st.columns(2)
                with cl:
                    latitude  = st.number_input("Latitude *",  value=45.5017, format="%.10f")
                with cg:
                    longitude = st.number_input("Longitude *", value=-73.5673, format="%.10f")
            radius   = st.number_input("Radius (m)", 1000, 50000, 10000, 1000)
            location = None
        submitted = st.form_submit_button("🔍 Search", use_container_width=True, type="primary")

    if submitted:
        if not business_type:
            st.error("❌ Business type is required!")
        elif search_type == "📍 By Location" and not location:
            st.error("❌ Location is required!")
        elif search_type == "🗺️ By Coordinates" and (not latitude or not longitude):
            st.error("❌ Coordinates are required!")
        else:
            with st.spinner("🔍 Searching…"):
                try:
                    if search_type == "🗺️ By Coordinates":
                        biz = st.session_state.places_service.search_nearby(
                            float(latitude), float(longitude), business_type, int(radius), 60
                        )
                        loc_str = f"Lat: {latitude}, Lng: {longitude}"
                    else:
                        biz = st.session_state.places_service.search_by_text(
                            f"{business_type} in {location}", location=location, max_results=60
                        )
                        loc_str = location

                    bww = run_search(business_type, loc_str, biz, user["id"])
                    st.success(f"✅ Found {len(biz)} businesses, {len(bww)} without websites!")
                except Exception as e:
                    st.error(f"❌ Error: {e}")
                    import traceback
                    st.code(traceback.format_exc())

    if st.session_state.get("businesses"):
        display_results(st.session_state.businesses, st.session_state.businesses_without_website)
        render_enrich_section()

    # Past searches
    if st.session_state.db_engine:
        with st.expander("📊 Your past searches"):
            try:
                with st.session_state.db_engine.connect() as conn:
                    rows = conn.execute(text("""
                        SELECT business_type, location, search_type, created_at,
                               results_count, businesses_without_website
                        FROM search_queries
                        WHERE user_id = :uid
                        ORDER BY created_at DESC LIMIT 20
                    """), {"uid": user["id"]}).fetchall()
                if rows:
                    st.dataframe(
                        pd.DataFrame(rows, columns=[
                            "Business Type","Location","Type","Date","Total","Without Websites"
                        ]),
                        use_container_width=True, hide_index=True,
                    )
                else:
                    st.info("No searches yet.")
            except Exception as e:
                st.warning(f"Could not load past searches: {e}")


# ═════════════════════════════════════════════════════════════════════════════
# Page: Search by Map
# ═════════════════════════════════════════════════════════════════════════════
elif effective_page == "🗺️ Search by Map":
    st.title("🗺️ Interactive Map Search")

    if st.session_state.places_service is None:
        st.error("Google Places API key not configured.")
        st.stop()

    btype_map = st.text_input("Business Type *", placeholder="Hotels, Restaurants…", key="map_btype")
    c1, c2 = st.columns([3, 1])
    with c1:
        radius_km = st.slider("Radius (km)", 1, 20, 5, 1)
    with c2:
        st.metric("Radius", f"{radius_km * 1000:,} m")

    if "map_center" not in st.session_state:
        st.session_state.map_center = [45.5017, -73.5673]
    cur = st.session_state.map_center.copy()

    st.info("💡 Click anywhere on the map to set the search location.")
    m = folium.Map(location=cur, zoom_start=10, tiles="OpenStreetMap")
    folium.Marker(cur, popup=f"Lat: {cur[0]:.6f}<br>Lng: {cur[1]:.6f}",
                  icon=folium.Icon(color="red", icon="info-sign")).add_to(m)
    md = st_folium(m, width="100%", height=500, returned_objects=["last_clicked"], key="imap")

    if md and md.get("last_clicked"):
        clat, clng = md["last_clicked"]["lat"], md["last_clicked"]["lng"]
        if abs(clat - cur[0]) > 0.0001 or abs(clng - cur[1]) > 0.0001:
            st.session_state.map_center = [clat, clng]
            st.success(f"📍 Location set: {clat:.6f}, {clng:.6f}")
            st.rerun()

    a1, a2, a3 = st.columns([2, 2, 1])
    with a1:
        mlat = st.number_input("Latitude",  value=cur[0], format="%.10f", step=0.0001, key="mlat")
    with a2:
        mlng = st.number_input("Longitude", value=cur[1], format="%.10f", step=0.0001, key="mlng")
    with a3:
        st.write(""); st.write("")
        if st.button("📍 Update", type="secondary"):
            st.session_state.map_center = [mlat, mlng]
            st.rerun()

    slat, slng = st.session_state.map_center
    st.info(f"📍 Search will use: {slat:.6f}, {slng:.6f}")

    if st.button("🔍 Search at This Location", type="primary", use_container_width=True):
        if not btype_map:
            st.error("❌ Business type is required!")
        else:
            with st.spinner(f"🔍 Searching for {btype_map} within {radius_km}km…"):
                try:
                    biz = st.session_state.places_service.search_nearby(
                        float(slat), float(slng), btype_map, radius_km * 1000, 60
                    )
                    if biz:
                        bww = run_search(btype_map, f"Lat:{slat},Lng:{slng}", biz, user["id"])
                        st.session_state.search_location = [slat, slng]
                        st.success(f"✅ Found {len(biz)} businesses!")
                        st.rerun()
                    else:
                        st.warning("No businesses found in this area.")
                except Exception as e:
                    st.error(f"❌ {e}")

    if st.session_state.get("businesses") and st.session_state.get("search_location"):
        biz = st.session_state.businesses
        sloc = st.session_state.search_location

        rm = folium.Map(location=sloc, zoom_start=12)
        folium.Marker(sloc, popup="Search Center",
                      icon=folium.Icon(color="red", icon="info-sign", prefix="fa")).add_to(rm)
        for b in biz:
            if b.get("latitude") and b.get("longitude"):
                color = "green" if b.get("has_website") else "blue"
                folium.Marker(
                    [b["latitude"], b["longitude"]],
                    popup=folium.Popup(
                        f"<b>{b.get('name','')}</b><br>"
                        f"{'✅ Website' if b.get('has_website') else '❌ No Website'}<br>"
                        f"Rating: {b.get('rating','N/A')}", max_width=260
                    ),
                    tooltip=b.get("name", ""),
                    icon=folium.Icon(color=color, icon="check" if b.get("has_website") else "question", prefix="fa"),
                ).add_to(rm)
        st_folium(rm, width="100%", height=500, key="results_map")
        display_results(biz, st.session_state.businesses_without_website)
        render_enrich_section()


# ═════════════════════════════════════════════════════════════════════════════
# Page: Pricing
# ═════════════════════════════════════════════════════════════════════════════
elif effective_page == "💳 Plans & Pricing":
    render_pricing_page(user, st.session_state.billing_service)
