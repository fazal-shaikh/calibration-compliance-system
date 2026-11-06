"""
Main Application Entry Point
Streamlit multi-page enterprise application for Calibration Management,
Certificate Tracking, and Prevention of Overdue Instrument Usage.
"""

import os
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent))

import streamlit as st
from database.connection import SessionLocal
from dashboard.overview import render_overview
from dashboard.instruments import render_instruments
from dashboard.calibration import render_calibration
from dashboard.production import render_production
from dashboard.work_orders import render_work_orders
from dashboard.alerts import render_alerts
from dashboard.audit import render_audit
from dashboard.data_quality import render_data_quality

st.set_page_config(
    page_title="Calibration Management & Compliance System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished enterprise look
st.markdown("""
<style>
    .main-header {
        font-size: 26px;
        font-weight: 700;
        color: #1E3A8A;
        margin-bottom: 0px;
    }
    .sub-header {
        font-size: 14px;
        color: #64748B;
        margin-bottom: 20px;
    }
    .metric-card {
        background-color: #F8FAFC;
        border-radius: 8px;
        padding: 16px;
        border-left: 5px solid #2563EB;
    }
</style>
""", unsafe_allow_html=True)

# Database Session Management
@st.cache_resource
def get_db_session():
    return SessionLocal()

db = get_db_session()

# Sidebar Navigation
st.sidebar.image("https://img.icons8.com/fluency/96/shield.png", width=64)
st.sidebar.title("Compliance System")
st.sidebar.caption("Enterprise Metrology & Gatekeeper v2.4")

PAGE_OPTIONS = [
    "1. Executive Dashboard",
    "2. Instrument Management",
    "3. Calibration Management",
    "4. Production Usage",
    "5. Work Orders and CAPA",
    "6. Alerts and Compliance",
    "7. Audit History",
    "8. Data Quality & Benchmarks"
]

selected_page = st.sidebar.radio("Navigate Application", PAGE_OPTIONS)

st.sidebar.markdown("---")
st.sidebar.markdown("**System Metadata**")
st.sidebar.caption("• Target DB: SQLite (Portable)")
st.sidebar.caption("• Reproducibility Seed: `20261022`")
st.sidebar.caption("• Gatekeeper Policy: `ISO/IEC 17025`")
st.sidebar.caption("• Active Work Orders & Gate: `Enforced`")

# Route to selected page
try:
    if selected_page == "1. Executive Dashboard":
        render_overview(db)
    elif selected_page == "2. Instrument Management":
        render_instruments(db)
    elif selected_page == "3. Calibration Management":
        render_calibration(db)
    elif selected_page == "4. Production Usage":
        render_production(db)
    elif selected_page == "5. Work Orders and CAPA":
        render_work_orders(db)
    elif selected_page == "6. Alerts and Compliance":
        render_alerts(db)
    elif selected_page == "7. Audit History":
        render_audit(db)
    elif selected_page == "8. Data Quality & Benchmarks":
        render_data_quality(db)
except Exception as e:
    st.error(f"Error rendering page: {e}")
    import traceback
    st.code(traceback.format_exc())