"""
Dashboard Page: Calibration Management
Tracks empirical calibration tests, deviation tolerance curves, certificates, and test recording.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database.models import Asset, CalibrationEvent, Certificate, CalibrationPlan
from services.calibration_service import CalibrationService

def render_calibration(db):
    st.title("📐 Calibration Management & Certificate Tracking")
    st.markdown("Monitor empirical calibration measurements, tolerance limits, certificate registries, and record new tests.")

    cal_service = CalibrationService(db)

    tab1, tab2, tab3 = st.tabs(["📜 Calibration Events", "🪪 Certificates Registry", "✍️ Record New Calibration"])

    with tab1:
        st.subheader("Historical Calibration Test Records")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            res_filter = st.selectbox("Result Filter", ["ALL", "PASS", "FAIL"])
        with col_f2:
            asset_search = st.text_input("Filter by Asset ID", "")

        query = db.query(
            CalibrationEvent.calibration_id,
            CalibrationEvent.asset_id,
            CalibrationEvent.calibration_date,
            CalibrationEvent.technician,
            CalibrationEvent.measured_value,
            CalibrationEvent.reference_value,
            CalibrationEvent.tolerance,
            CalibrationEvent.deviation,
            CalibrationEvent.result,
            CalibrationEvent.notes
        )

        if res_filter != "ALL":
            query = query.filter(CalibrationEvent.result == res_filter)
        if asset_search:
            query = query.filter(CalibrationEvent.asset_id.ilike(f"%{asset_search}%"))

        records = query.order_by(CalibrationEvent.calibration_date.desc()).limit(200).all()
        df = pd.DataFrame(records, columns=[
            "Calibration ID", "Asset ID", "Date", "Technician",
            "Measured", "Reference", "Tolerance", "Deviation", "Result", "Notes"
        ])
        st.dataframe(df, use_container_width=True, height=350)

        # Plot Deviation vs Tolerance scatter
        if not df.empty:
            st.markdown("#### Measurement Deviation vs. Allowable Tolerance Limit")
            fig = px.scatter(
                df.head(100),
                x="Tolerance",
                y="Deviation",
                color="Result",
                hover_data=["Asset ID", "Calibration ID", "Technician"],
                color_discrete_map={"PASS": "#28a745", "FAIL": "#dc3545"},
                title="Top 100 Recent Tests: Deviation vs Tolerance Envelope"
            )
            fig.update_layout(height=350, margin=dict(t=30, b=10, l=10, r=10))
            st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.subheader("Metrology Certificates Registry")
        cert_rows = db.query(
            Certificate.certificate_id,
            Certificate.certificate_number,
            Certificate.calibration_id,
            Certificate.asset_id,
            Certificate.issue_date,
            Certificate.expiry_date,
            Certificate.verification_status,
            Certificate.issuer_name
        ).order_by(Certificate.issue_date.desc()).limit(200).all()

        cert_df = pd.DataFrame(cert_rows, columns=[
            "Certificate ID", "Cert Number", "Calibration ID", "Asset ID",
            "Issue Date", "Expiry Date", "Status", "Issuer"
        ])
        st.dataframe(cert_df, use_container_width=True, height=350)

    with tab3:
        st.subheader("Execute New Calibration Test")
        with st.form("new_cal_form"):
            asset_ids = [r[0] for r in db.query(Asset.asset_id).all()]
            sel_asset = st.selectbox("Select Target Asset", asset_ids)
            
            # Lookup asset plan
            target_asset = db.query(Asset).filter(Asset.asset_id == sel_asset).first()
            plan = db.query(CalibrationPlan).filter(CalibrationPlan.plan_id == target_asset.plan_id).first() if target_asset else None
            plan_tol = plan.tolerance if plan else 0.05
            st.info(f"Target Plan: {plan.name if plan else 'N/A'} | Allowable Tolerance: ±{plan_tol}")

            col_m1, col_m2 = st.columns(2)
            with col_m1:
                ref_val = st.number_input("Standard Reference Value", value=100.0, step=0.1)
            with col_m2:
                meas_val = st.number_input("Observed Measured Value", value=100.02, step=0.01)

            col_t1, col_t2 = st.columns(2)
            with col_t1:
                technician = st.text_input("Lead Metrologist", "Sarah Chen (Lead Metrologist)")
            with col_t2:
                notes = st.text_input("Environmental / Test Notes", "Standard test conducted at 22°C, 45% RH")

            submit_cal = st.form_submit_button("Submit & Evaluate Calibration Test")

            if submit_cal:
                res = cal_service.record_calibration(
                    asset_id=sel_asset,
                    measured_value=meas_val,
                    reference_value=ref_val,
                    technician=technician,
                    notes=notes
                )
                if res["result"] == "PASS":
                    st.success(f"Calibration PASSED! Deviation: {res['calibration_event'].deviation:.4f} <= Tolerance: {plan_tol}. Certificate {res['certificate'].certificate_number} issued!")
                else:
                    st.error(f"Calibration FAILED! Deviation: {res['calibration_event'].deviation:.4f} > Tolerance: {plan_tol}. Asset Quarantined! CAPA and Impact Assessment created!")
                st.rerun()