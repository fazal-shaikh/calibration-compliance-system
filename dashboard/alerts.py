"""
Dashboard Page: Alerts & Compliance Monitoring
Prioritized compliance hazard monitoring, overdue warnings, and alert lifecycle management.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database.models import Alert
from business_logic.alerts import acknowledge_alert, resolve_alert

def render_alerts(db):
    st.title("🚨 Compliance Alerts & Hazard Monitoring")
    st.markdown("Early warning system for impending calibration deadlines, critical failures, and unauthorized usage attempts.")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        sev_filter = st.selectbox("Severity Filter", ["ALL", "CRITICAL", "HIGH", "MEDIUM", "LOW"])
    with col_f2:
        status_filter = st.selectbox("Status Filter", ["ALL", "ACTIVE", "ACKNOWLEDGED", "RESOLVED"])

    query = db.query(Alert)
    if sev_filter != "ALL":
        query = query.filter(Alert.severity == sev_filter)
    if status_filter != "ALL":
        query = query.filter(Alert.status == status_filter)

    alerts = query.order_by(Alert.created_at.desc()).all()

    alert_data = [
        {
            "Alert ID": a.alert_id,
            "Asset ID": a.asset_id or "System",
            "Type": a.alert_type,
            "Severity": a.severity,
            "Message": a.message,
            "Status": a.status,
            "Created At": a.created_at.strftime("%Y-%m-%d %H:%M") if a.created_at else None
        }
        for a in alerts
    ]
    df = pd.DataFrame(alert_data)
    st.markdown(f"**Showing {len(df)} Compliance Alerts**")
    st.dataframe(df, use_container_width=True, height=350)

    # Action to acknowledge or resolve
    if not df.empty:
        st.subheader("Manage Alert Status")
        with st.form("alert_action_form"):
            col_a1, col_a2 = st.columns(2)
            with col_a1:
                sel_alert_id = st.selectbox("Select Alert", [a.alert_id for a in alerts])
            with col_a2:
                action = st.radio("Action", ["Acknowledge", "Resolve"])
            submit_action = st.form_submit_button("Update Alert")

            if submit_action:
                alert_obj = db.query(Alert).filter(Alert.alert_id == sel_alert_id).first()
                if alert_obj:
                    if action == "Acknowledge":
                        alert_obj.status = "ACKNOWLEDGED"
                        alert_obj.acknowledged_at = datetime.utcnow()
                    else:
                        alert_obj.status = "RESOLVED"
                        alert_obj.resolved_at = datetime.utcnow()
                    db.commit()
                    st.success(f"Alert {sel_alert_id} marked as {alert_obj.status}!")
                    st.rerun()