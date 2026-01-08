import streamlit as st
from utils.supabase_client import supabase

def admin_dashboard():
    st.title("🛠️ Admin Dashboard")

    logs = supabase.table("support_audit_logs").select("*").execute().data

    total = len(logs)
    high = sum(1 for l in logs if l["urgency"] == "high")
    escalated = sum(1 for l in logs if l["escalate"])

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Tickets", total)
    col2.metric("High Urgency", high)
    col3.metric("Escalations", escalated)

    st.markdown("### 🔥 Escalation Rate")
    st.progress(int((escalated / max(total,1)) * 100))
