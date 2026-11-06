"""
Dashboard Page: Production Usage & Gatekeeper Simulator
Real-time shopfloor transaction log and live interactive compliance gate simulator.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from database.models import Asset, ProductionUse
from services.production_service import ProductionService

def render_production(db):
    st.title("🛡️ Production Usage & Shopfloor Gatekeeper")
    st.markdown("Prevents uncalibrated, expired, or prohibited instrument usage in active manufacturing lines.")

    prod_service = ProductionService(db)

    tab1, tab2 = st.tabs(["🚀 Live Gatekeeper Simulator", "📜 Historical Usage Logs"])

    with tab1:
        st.subheader("Shopfloor Usage Gatekeeper Authorization Check")
        st.markdown(
            "Before an operator can engage an instrument in a production run, the system validates:"
            " **(1) Existence (2) Active Status (3) Calibration Validity (4) Due Date Window (5) Certificate (6) Latest Result (7) No Blocking WOs (8) Emergency Extension.**"
        )

        with st.form("gatekeeper_sim"):
            col_g1, col_g2 = st.columns(2)
            with col_g1:
                asset_list = [r[0] for r in db.query(Asset.asset_id).all()]
                target_asset = st.selectbox("Select Target Asset Tag", asset_list)
                batch_id = st.text_input("Production Batch Lot ID", "BATCH-2026-9042")
            with col_g2:
                prod_line = st.selectbox("Manufacturing Line", [f"Line-{i:02d}" for i in range(1, 11)])
                operator_id = st.text_input("Operator Badge ID", "OP-1042")

            submit_gate = st.form_submit_button("🛡️ Validate & Authorize Instrument Usage")

            if submit_gate:
                res = prod_service.validate_and_record_usage(
                    asset_id=target_asset,
                    batch_id=batch_id,
                    production_line=prod_line,
                    operator_id=operator_id,
                    usage_timestamp=datetime.utcnow()
                )

                decision = res["decision"]
                if decision == "ALLOWED":
                    st.success(f"✅ USAGE GRANTED: {res['reason']} (Policy: {res['policy_applied']})")
                elif decision == "ALLOWED_WITH_EXCEPTION":
                    st.warning(f"⚠️ USAGE GRANTED WITH EXCEPTION: {res['reason']} (Policy: {res['policy_applied']})")
                else:
                    st.error(f"🛑 USAGE BLOCKED: {res['reason']} (Policy: {res['policy_applied']})")

    with tab2:
        st.subheader("Production Usage Transactions Log")
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            dec_filter = st.selectbox("Filter Decision", ["ALL", "ALLOWED", "BLOCKED", "ALLOWED_WITH_EXCEPTION"])
        with col_f2:
            asset_search = st.text_input("Search Asset or Batch", "")

        query = db.query(
            ProductionUse.usage_id,
            ProductionUse.asset_id,
            ProductionUse.usage_timestamp,
            ProductionUse.batch_id,
            ProductionUse.production_line,
            ProductionUse.operator_id,
            ProductionUse.decision,
            ProductionUse.policy_applied,
            ProductionUse.reason
        )

        if dec_filter != "ALL":
            query = query.filter(ProductionUse.decision == dec_filter)
        if asset_search:
            query = query.filter(
                (ProductionUse.asset_id.ilike(f"%{asset_search}%")) |
                (ProductionUse.batch_id.ilike(f"%{asset_search}%"))
            )

        uses = query.order_by(ProductionUse.usage_timestamp.desc()).limit(300).all()
        use_df = pd.DataFrame(uses, columns=[
            "Usage ID", "Asset ID", "Timestamp", "Batch ID",
            "Line", "Operator", "Decision", "Policy Code", "Reason"
        ])
        st.dataframe(use_df, use_container_width=True, height=400)