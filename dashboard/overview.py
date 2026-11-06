"""
Dashboard Page: Executive Overview
High-level KPIs, compliance scorecards, failure rates, downtime, and operational charts.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
from database.models import Asset, CalibrationEvent, Certificate, WorkOrder, ProductionUse
from validation.evaluation import evaluate_metrics

def render_overview(db):
    st.title("🏭 Executive Calibration & Compliance Dashboard")
    st.markdown("Real-time operational intelligence, regulatory compliance tracking, and metrology KPIs.")

    sim_date = datetime(2026, 11, 1, 17, 0, 0)
    metrics = evaluate_metrics(db, sim_date)

    total_assets = db.query(Asset).count()
    active_assets = db.query(Asset).filter(Asset.status == "ACTIVE").count()
    total_wos = db.query(WorkOrder).count()

    # Row 1: KPI Cards
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric(
            label="Total Instruments",
            value=f"{total_assets:,}",
            delta=f"{active_assets} Active"
        )
    with col2:
        st.metric(
            label="Calibration Compliance",
            value=f"{metrics['calibration_compliance_rate']}%",
            delta=f"{metrics['overdue_instrument_percentage']}% Overdue",
            delta_color="inverse"
        )
    with col3:
        st.metric(
            label="Certificate Completeness",
            value=f"{metrics['certificate_completeness_rate']}%",
            delta="ISO/IEC 17025"
        )
    with col4:
        st.metric(
            label="Total Downtime",
            value=f"{metrics['total_downtime_hours']} hrs",
            delta=f"{metrics['mean_time_to_repair_hours']}h MTTR"
        )
    with col5:
        st.metric(
            label="Prohibited Usages",
            value=f"{metrics['prohibited_usage_count']}",
            delta="Blocked / Intercepted",
            delta_color="inverse"
        )

    st.markdown("---")

    # Row 2: Charts
    col_c1, col_c2 = st.columns(2)

    with col_c1:
        st.subheader("📊 Asset Distribution by Status")
        asset_rows = db.query(Asset.status).all()
        status_counts = pd.Series([r[0] for r in asset_rows]).value_counts().reset_index()
        status_counts.columns = ["Status", "Count"]

        fig_status = px.pie(
            status_counts,
            values="Count",
            names="Status",
            color="Status",
            color_discrete_map={
                "ACTIVE": "#28a745",
                "IN_CALIBRATION": "#17a2b8",
                "QUARANTINED": "#dc3545",
                "OUT_OF_SERVICE": "#ffc107",
                "RETIRED": "#6c757d"
            },
            hole=0.45
        )
        fig_status.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_status, use_container_width=True)

    with col_c2:
        st.subheader("⚙️ Calibration Outcomes (PASS vs FAIL)")
        cal_rows = db.query(CalibrationEvent.result).all()
        cal_counts = pd.Series([r[0] for r in cal_rows]).value_counts().reset_index()
        cal_counts.columns = ["Result", "Count"]

        fig_cal = px.bar(
            cal_counts,
            x="Result",
            y="Count",
            color="Result",
            color_discrete_map={"PASS": "#28a745", "FAIL": "#dc3545"},
            text="Count"
        )
        fig_cal.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_cal, use_container_width=True)

    # Row 3: Shopfloor Gatekeeper Summary
    col_d1, col_d2 = st.columns(2)

    with col_d1:
        st.subheader("🛡️ Production Usage Gatekeeper Decisions")
        use_rows = db.query(ProductionUse.decision).all()
        use_counts = pd.Series([r[0] for r in use_rows]).value_counts().reset_index()
        use_counts.columns = ["Decision", "Count"]

        fig_use = px.pie(
            use_counts,
            values="Count",
            names="Decision",
            color="Decision",
            color_discrete_map={
                "ALLOWED": "#28a745",
                "BLOCKED": "#dc3545",
                "ALLOWED_WITH_EXCEPTION": "#ffc107"
            },
            hole=0.4
        )
        fig_use.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300)
        st.plotly_chart(fig_use, use_container_width=True)

    with col_d2:
        st.subheader("⏱️ Maintenance Downtime by Order Type")
        wo_rows = db.query(WorkOrder.order_type, WorkOrder.downtime_hours).all()
        wo_df = pd.DataFrame(wo_rows, columns=["Order Type", "Downtime (Hours)"])
        grouped_wo = wo_df.groupby("Order Type")["Downtime (Hours)"].sum().reset_index()

        fig_dt = px.bar(
            grouped_wo,
            x="Order Type",
            y="Downtime (Hours)",
            color="Order Type",
            text="Downtime (Hours)"
        )
        fig_dt.update_layout(margin=dict(t=10, b=10, l=10, r=10), height=300, showlegend=False)
        st.plotly_chart(fig_dt, use_container_width=True)