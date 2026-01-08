# dashboards/admin.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.supabase_client import supabase

def admin_dashboard():
    st.title("👑 Admin Dashboard")

    # ---------------- USERS SUMMARY ----------------
    users = supabase.table("users").select("*").execute().data
    total_users = len(users)
    admins = len([u for u in users if u.get("role")=="admin"])
    agents = len([u for u in users if u.get("role")=="agent"])
    managers = len([u for u in users if u.get("role")=="manager"])

    st.subheader("🧑‍🤝‍🧑 Users Summary")
    st.metric("Total Users", total_users)
    st.metric("Admins", admins)
    st.metric("Agents", agents)
    st.metric("Managers", managers)

    # ---------------- ESCALATIONS TREND ----------------
    logs = supabase.table("support_audit_logs").select("*").order("created_at", desc=False).execute().data
    df = pd.DataFrame(logs)

    if not df.empty:
        df['created_at'] = pd.to_datetime(df['created_at'])
        df['date'] = df['created_at'].dt.date
        escalations = df[df['escalate']==True].groupby('date').size().reset_index(name='count')
        st.subheader("🚨 Escalations Trend")
        fig = px.line(escalations, x='date', y='count', markers=True, title="Escalations over time")
        st.plotly_chart(fig, use_container_width=True)

        # Urgency breakdown
        st.subheader("📊 Urgency Breakdown")
        urgency_counts = df['urgency'].value_counts().reset_index()
        urgency_counts.columns = ['urgency','count']
        fig2 = px.pie(urgency_counts, names='urgency', values='count', title='Tickets by Urgency', color='urgency')
        st.plotly_chart(fig2, use_container_width=True)

        # Total escalations
        total_escalations = df[df['escalate']==True].shape[0]
        st.metric("Total Escalations", total_escalations)

    else:
        st.info("No ticket data yet.")
