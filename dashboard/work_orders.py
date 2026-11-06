"""
Dashboard Page: Work Orders, CAPA & Impact Assessments
Tracks maintenance interventions, corrective actions, downtime, and failure impact reviews.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database.models import WorkOrder, CorrectiveAction, ImpactAssessment

def render_work_orders(db):
    st.title("🔧 Work Orders, CAPA & Impact Investigations")
    st.markdown("Manage proactive maintenance, failure remediation, retrospective lot tracing, and downtime.")

    tab1, tab2, tab3 = st.tabs(["📋 Work Orders", "🛡️ Impact Assessments", "🔍 Corrective Actions (CAPA)"])

    with tab1:
        st.subheader("Maintenance & Calibration Work Orders")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            wo_status_filter = st.selectbox("Filter Status", ["ALL", "OPEN", "IN_PROGRESS", "COMPLETED", "CANCELLED"])
        with col_f2:
            wo_type_filter = st.selectbox("Filter Type", ["ALL", "FAILED_CALIBRATION", "OVERDUE_CALIBRATION", "UPCOMING_CALIBRATION", "CORRECTIVE_MAINTENANCE"])

        query = db.query(
            WorkOrder.work_order_id,
            WorkOrder.asset_id,
            WorkOrder.order_type,
            WorkOrder.priority,
            WorkOrder.status,
            WorkOrder.assigned_technician,
            WorkOrder.creation_date,
            WorkOrder.completion_date,
            WorkOrder.downtime_hours,
            WorkOrder.cost,
            WorkOrder.resolution_notes
        )

        if wo_status_filter != "ALL":
            query = query.filter(WorkOrder.status == wo_status_filter)
        if wo_type_filter != "ALL":
            query = query.filter(WorkOrder.order_type == wo_type_filter)

        wos = query.order_by(WorkOrder.creation_date.desc()).all()
        wo_df = pd.DataFrame(wos, columns=[
            "WO ID", "Asset ID", "Type", "Priority", "Status",
            "Technician", "Created", "Completed", "Downtime (h)", "Cost ($)", "Notes"
        ])
        st.dataframe(wo_df, use_container_width=True, height=350)

    with tab2:
        st.subheader("Retrospective Impact Assessments (Post-Failure Lot Tracing)")
        ia_rows = db.query(
            ImpactAssessment.assessment_id,
            ImpactAssessment.calibration_id,
            ImpactAssessment.asset_id,
            ImpactAssessment.investigation_status,
            ImpactAssessment.risk_level,
            ImpactAssessment.affected_batches_count,
            ImpactAssessment.affected_usage_events_count,
            ImpactAssessment.disposition,
            ImpactAssessment.assessor,
            ImpactAssessment.assessment_date
        ).order_by(ImpactAssessment.assessment_date.desc()).all()

        ia_df = pd.DataFrame(ia_rows, columns=[
            "Assessment ID", "Calibration ID", "Asset ID", "Investigation Status",
            "Risk Level", "Affected Batches", "Affected Uses", "Disposition", "Assessor", "Date"
        ])
        st.dataframe(ia_df, use_container_width=True, height=350)

    with tab3:
        st.subheader("Corrective & Preventive Actions (CAPA)")
        capa_rows = db.query(
            CorrectiveAction.corrective_action_id,
            CorrectiveAction.calibration_id,
            CorrectiveAction.asset_id,
            CorrectiveAction.status,
            CorrectiveAction.root_cause,
            CorrectiveAction.containment_action,
            CorrectiveAction.preventive_action,
            CorrectiveAction.assigned_to,
            CorrectiveAction.target_date
        ).order_by(CorrectiveAction.created_at.desc()).all()

        capa_df = pd.DataFrame(capa_rows, columns=[
            "CAPA ID", "Calibration ID", "Asset ID", "Status",
            "Root Cause", "Containment Action", "Preventive Action", "Assigned Lead", "Target Date"
        ])
        st.dataframe(capa_df, use_container_width=True, height=350)