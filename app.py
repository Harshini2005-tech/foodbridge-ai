
import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone
from supabase import create_client

st.set_page_config(
    page_title="FoodBridge AI",
    page_icon="🍲",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
    background: #f5faf6;
}
h1, h2, h3 {
    color: #176344;
}
[data-testid="stMetric"] {
    background: white;
    padding: 14px;
    border-radius: 12px;
    border: 1px solid #d8e9dd;
}
</style>
""", unsafe_allow_html=True)

st.title("🍲 FoodBridge AI")
st.subheader("Community Food Donation & Surplus Management")
st.write(
    "Connect surplus food with community organizations. "
    "Register donations and track their availability."
)

# Connect to the hosted database when credentials are configured.
def get_database():
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        if not url or not key:
            return None
        return create_client(url, key)
    except Exception:
        return None

db = get_database()

if db is None:
    st.warning(
        "Database not connected yet. Complete the Supabase setup "
        "to enable persistent shared donations."
    )

page = st.sidebar.radio(
    "Menu",
    ["Dashboard", "Register Donation", "About"]
)

def load_donations():
    if db is None:
        return []
    try:
        result = (
            db.table("donations")
            .select("*")
            .order("created_at", desc=True)
            .execute()
        )
        return result.data
    except Exception as error:
        st.error("Could not load donations. Check the database setup.")
        return []

if page == "Dashboard":
    st.header("Live Donation Dashboard")

    if st.button("🔄 Refresh donation list"):
        st.rerun()

    donations = load_donations()
    available = [
        item for item in donations
        if item.get("status") == "Available"
    ]

    c1, c2, c3 = st.columns(3)
    c1.metric("Total donations", len(donations))
    c2.metric("Available donations", len(available))
    c3.metric(
        "Available portions",
        sum(int(item.get("quantity", 0)) for item in available)
    )

    st.subheader("Latest donations")

    if donations:
        df = pd.DataFrame(donations)
        columns = [
            column for column in [
                "donor_name", "food_name", "quantity",
                "location", "prepared_at", "status"
            ] if column in df.columns
        ]
        st.dataframe(
            df[columns],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info(
            "No donations found yet. Register a donation "
            "after connecting the database."
        )

elif page == "Register Donation":
    st.header("Register Surplus Food")

    with st.form("donation_form"):
        donor = st.text_input("Donor or organization name")
        food = st.selectbox(
            "Food type",
            ["Cooked meals", "Rice", "Bread", "Vegetables",
             "Fruits", "Packaged food", "Other"]
        )
        quantity = st.number_input(
            "Number of meal portions",
            min_value=1,
            max_value=10000,
            value=25
        )
        location = st.text_input("Collection area or city")
        prepared_at = st.time_input(
            "Food preparation time",
            value=datetime.now().time().replace(
                second=0, microsecond=0
            )
        )

        submitted = st.form_submit_button(
            "Register donation",
            type="primary"
        )

    if submitted:
        if not donor.strip() or not location.strip():
            st.error("Enter the donor name and collection area.")
        elif db is None:
            st.error(
                "Database not connected. Set up Supabase first "
                "so your donation can be saved permanently."
            )
        else:
            record = {
                "donor_name": donor.strip(),
                "food_name": food,
                "quantity": int(quantity),
                "location": location.strip(),
                "prepared_at": prepared_at.strftime("%H:%M"),
                "status": "Available",
                "created_at": datetime.now(
                    timezone.utc
                ).isoformat()
            }
            try:
                db.table("donations").insert(record).execute()
                st.success(
                    "Donation saved! Open Dashboard to see it."
                )
            except Exception:
                st.error(
                    "Could not save the donation. Check your "
                    "database table and permissions."
                )

elif page == "About":
    st.header("About FoodBridge AI")
    st.write("""
    **Problem:** Edible surplus food may be wasted while
    communities need food assistance.

    **Solution:** A shared donation platform that registers
    available food and tracks donation quantities.

    **Current modules**
    - Donation registration
    - Persistent database storage
    - Shared donation dashboard
    - Availability and quantity summaries

    **Technology**
    - Python
    - Streamlit
    - Supabase
    - Pandas

    The machine-learning surplus predictor will be added after
    the database and data collection pipeline are working.
    """)
  
