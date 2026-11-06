"""
Dashboard Page: Audit Trail & Traceability Ledger
Immutable append-only record of all system modifications, status changes, and administrative actions.
"""

import json
import streamlit as st
import pandas as pd
from database.models import AuditRecord

def render_audit(db):
    st.title("📜 Audit Trail & Regulatory Traceability Ledger")
    st.markdown("Immutable record of system events, operator actions, status transitions, and data mutations.")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        table_filter = st.selectbox(
            "Filter Entity Table",
            ["ALL"] + [r[0] for r in db.query(AuditRecord.table_name).distinct().all()]
        )
    with col_f2:
        action_filter = st.selectbox("Filter Action", ["ALL", "INSERT", "UPDATE", "DELETE"])

    query = db.query(AuditRecord)
    if table_filter != "ALL":
        query = query.filter(AuditRecord.table_name == table_filter)
    if action_filter != "ALL":
        query = query.filter(AuditRecord.action == action_filter)

    records = query.order_by(AuditRecord.timestamp.desc()).limit(200).all()

    audit_data = [
        {
            "Audit ID": r.audit_id,
            "Table": r.table_name,
            "Record ID": r.record_id,
            "Action": r.action,
            "Actor": r.actor,
            "Timestamp": r.timestamp.strftime("%Y-%m-%d %H:%M:%S") if r.timestamp else None,
            "Reason": r.reason
        }
        for r in records
    ]
    df = pd.DataFrame(audit_data)
    st.dataframe(df, use_container_width=True, height=350)

    # Detailed record inspector
    if records:
        st.subheader("🔍 Inspect State Snapshot (Old vs New)")
        sel_audit_id = st.selectbox("Select Audit Record to Inspect", [r.audit_id for r in records])
        selected_record = next(r for r in records if r.audit_id == sel_audit_id)

        col_s1, col_s2 = st.columns(2)
        with col_s1:
            st.markdown("#### Pre-Mutation State (Old Values)")
            if selected_record.old_values_json:
                st.json(json.loads(selected_record.old_values_json))
            else:
                st.info("None (Initial INSERT)")
        with col_s2:
            st.markdown("#### Post-Mutation State (New Values)")
            if selected_record.new_values_json:
                st.json(json.loads(selected_record.new_values_json))
            else:
                st.info("None (Record Deleted)")