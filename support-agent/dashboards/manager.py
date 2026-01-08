import streamlit as st
from utils.supabase_client import supabase

def manager_dashboard():
    st.title("📊 Manager Dashboard")

    data = (
        supabase.table("support_audit_logs")
        .select("urgency, escalate")
        .execute()
        .data
    )

    total = len(data)
    escalations = sum(1 for d in data if d["escalate"])

    col1, col2 = st.columns(2)
    col1.metric("Total Tickets", total)
    col2.metric("Escalations", escalations)

    st.progress(int((escalations / max(total,1)) * 100))
