# dashboards/manager.py
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.supabase_client import supabase

def manager_dashboard():
    st.title("📈 Manager Dashboard")

    # ---------------- LOGS TREND ----------------
    logs = supabase.table("support_audit_logs").select("*").order("created_at", desc=False).execute().data
    df = pd.DataFrame(logs)

    if df.empty:
        st.info("No tickets analyzed yet.")
        return

    df['created_at'] = pd.to_datetime(df['created_at'])
    df['date'] = df['created_at'].dt.date

    # Escalation trend
    escalations = df[df['escalate']==True].groupby('date').size().reset_index(name='count')
    st.subheader("🚨 Escalations Trend")
    fig = px.bar(escalations, x='date', y='count', title="Escalations per day", color='count')
    st.plotly_chart(fig, use_container_width=True)

    # Confidence distribution
    st.subheader("📊 Confidence Distribution")
    fig2 = px.histogram(df, x='confidence', nbins=10, title="Confidence of AI Decisions", color='confidence')
    st.plotly_chart(fig2, use_container_width=True)

    # Tickets by category
    st.subheader("🏷️ Tickets by Category")
    cat_counts = df['category'].value_counts().reset_index()
    cat_counts.columns = ['category','count']
    fig3 = px.pie(cat_counts, names='category', values='count', title='Tickets by Category')
    st.plotly_chart(fig3, use_container_width=True)
