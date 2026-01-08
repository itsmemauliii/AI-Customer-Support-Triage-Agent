import stripe
import streamlit as st
import pandas as pd
import plotly.express as px
from utils.supabase_client import supabase

# ---- Stripe Setup ----
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]  # Add this in Streamlit secrets

def admin_dashboard():
    st.title("👑 Admin Dashboard")

    # ---------------- STRIPE BILLING ----------------
    st.subheader("💰 Stripe Revenue Overview")

    try:
        # Retrieve last 50 payments
        payments = stripe.PaymentIntent.list(limit=50)
        payment_data = []
        for p in payments.data:
            payment_data.append({
                "amount": p.amount / 100,  # Stripe amount is in cents
                "currency": p.currency.upper(),
                "status": p.status,
                "created": pd.to_datetime(p.created, unit='s')
            })
        df_payments = pd.DataFrame(payment_data)
        if not df_payments.empty:
            total_revenue = df_payments[df_payments['status']=='succeeded']['amount'].sum()
            st.metric("💵 Total Revenue", f"${total_revenue:,.2f}")

            # Revenue trend chart
            df_payments['date'] = df_payments['created'].dt.date
            revenue_trend = df_payments[df_payments['status']=='succeeded'].groupby('date')['amount'].sum().reset_index()
            fig_rev = px.line(revenue_trend, x='date', y='amount', markers=True, title="Revenue Trend")
            st.plotly_chart(fig_rev, use_container_width=True)
        else:
            st.info("No Stripe payments yet.")
    except Exception as e:
        st.error(f"⚠️ Error fetching Stripe data: {e}")

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

        st.subheader("📊 Urgency Breakdown")
        urgency_counts = df['urgency'].value_counts().reset_index()
        urgency_counts.columns = ['urgency','count']
        fig2 = px.pie(urgency_counts, names='urgency', values='count', title='Tickets by Urgency', color='urgency')
        st.plotly_chart(fig2, use_container_width=True)

        total_escalations = df[df['escalate']==True].shape[0]
        st.metric("Total Escalations", total_escalations)

    else:
        st.info("No ticket data yet.")
