"""
Dashboard Page: Instrument Management
Interactive registry of physical instruments, status workflows, and emergency extensions.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
from database.models import Asset, InstrumentType, CalibrationPlan, Supplier, CalibrationExtension
from services.instrument_service import InstrumentService

def render_instruments(db):
    st.title("🔬 Instrument Registry & Asset Lifecycle")
    st.markdown("Search, filter, inspect, and manage physical measurement assets across manufacturing lines.")

    inst_service = InstrumentService(db)

    # Filter Bar
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        search_query = st.text_input("🔍 Search Asset ID / Serial / Name", "")
    with col_f2:
        category_filter = st.selectbox(
            "Category",
            ["ALL"] + [r[0] for r in db.query(InstrumentType.category).distinct().all()]
        )
    with col_f3:
        status_filter = st.selectbox(
            "Operational Status",
            ["ALL", "ACTIVE", "IN_CALIBRATION", "QUARANTINED", "OUT_OF_SERVICE", "RETIRED"]
        )
    with col_f4:
        dept_filter = st.selectbox(
            "Department",
            ["ALL"] + [r[0] for r in db.query(Asset.department).distinct().all()]
        )

    # Query Data
    query = db.query(
        Asset.asset_id,
        Asset.name,
        Asset.serial_number,
        InstrumentType.category,
        Asset.department,
        Asset.location,
        Asset.status,
        Asset.last_calibration_date,
        Asset.next_due_date
    ).join(InstrumentType)

    if search_query:
        search_fmt = f"%{search_query}%"
        query = query.filter(
            (Asset.asset_id.ilike(search_fmt)) |
            (Asset.serial_number.ilike(search_fmt)) |
            (Asset.name.ilike(search_fmt))
        )
    if category_filter != "ALL":
        query = query.filter(InstrumentType.category == category_filter)
    if status_filter != "ALL":
        query = query.filter(Asset.status == status_filter)
    if dept_filter != "ALL":
        query = query.filter(Asset.department == dept_filter)

    rows = query.all()
    df = pd.DataFrame(rows, columns=[
        "Asset ID", "Instrument Name", "Serial Number", "Category",
        "Department", "Location", "Status", "Last Calibration", "Next Due Date"
    ])

    st.markdown(f"**Showing {len(df):,} Instruments**")
    st.dataframe(df, use_container_width=True, height=350)

    st.markdown("---")
    st.subheader("🛠️ Instrument Operations & Emergency Extensions")

    col_op1, col_op2 = st.columns(2)

    with col_op1:
        st.markdown("#### Change Operational Status")
        with st.form("status_form"):
            selected_asset = st.selectbox("Select Target Asset", [r[0] for r in db.query(Asset.asset_id).all()])
            new_status = st.selectbox("New Status", ["ACTIVE", "IN_CALIBRATION", "OUT_OF_SERVICE", "QUARANTINED", "RETIRED"])
            status_reason = st.text_input("Operational Reason / Work Order Ref", "Scheduled maintenance overhaul")
            submit_status = st.form_submit_button("Update Status")

            if submit_status:
                inst_service.update_status(selected_asset, new_status, actor="Dashboard Operator", reason=status_reason)
                st.success(f"Status for {selected_asset} updated to {new_status}!")
                st.rerun()

    with col_op2:
        st.markdown("#### Grant Emergency Calibration Extension")
        with st.form("extension_form"):
            ext_asset = st.selectbox("Select Asset for Extension", [r[0] for r in db.query(Asset.asset_id).all()], key="ext_sel")
            ext_days = st.slider("Extension Duration (Days)", min_value=1, max_value=30, value=14)
            ext_approver = st.text_input("Authorized Approver", "Dr. Eleanor Vance (Director of Quality)")
            ext_just = st.text_area("Engineering Justification", "Critical batch run pending weekend calibration standard turnaround.")
            submit_ext = st.form_submit_button("Authorize & Grant Extension")

            if submit_ext:
                new_due = datetime.utcnow() + timedelta(days=ext_days)
                inst_service.grant_extension(ext_asset, new_due, ext_approver, ext_just)
                st.success(f"Emergency extension granted for {ext_asset} until {new_due.strftime('%Y-%m-%d')}!")
                st.rerun()