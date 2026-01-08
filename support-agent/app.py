# app.py
import streamlit as st
import pandas as pd
from graph.workflow import build_graph
from utils.supabase_client import supabase
from utils.auth import login, signup, logout
from dashboards.admin import admin_dashboard
from dashboards.manager import manager_dashboard
import stripe

# ---------------- CONFIG ----------------
CONFIDENCE_THRESHOLD = 0.6
st.set_page_config(page_title="AI Support Triage SaaS", layout="wide")

# ---------------- STRIPE ----------------
stripe.api_key = st.secrets["STRIPE_SECRET_KEY"]

def create_checkout_session(email):
    session = stripe.checkout.Session.create(
        customer_email=email,
        payment_method_types=["card"],
        line_items=[{
            "price": st.secrets["STRIPE_PRICE_ID"],
            "quantity": 1,
        }],
        mode="subscription",
        success_url=st.secrets["APP_URL"] + "/success",
        cancel_url=st.secrets["APP_URL"] + "/cancel",
    )
    return session.url

# ---------------- AUTH ----------------
if "user" not in st.session_state:
    st.write("## 🔐 Please login or sign up")
    tab1, tab2 = st.tabs(["Login", "Sign up"])
    with tab1:
        login()
    with tab2:
        signup()
    st.stop()

# ---------------- LOGOUT ----------------
st.sidebar.button("🔓 Logout", on_click=logout)

# ---------------- NAVIGATION ----------------
role = st.session_state["user"]["role"]
pages = ["Analyze Ticket", "Audit Logs"]
if role in ["manager"]:
    pages.append("Manager Dashboard")
if role in ["admin"]:
    pages.append("Admin Dashboard")

page = st.sidebar.radio("Navigation", pages)

# ==================================================
# 📊 PAGE: Analyze Ticket
# ==================================================
if page == "Analyze Ticket":
    st.title("🎧 AI Support Triage Agent")
    ticket = st.text_area("Paste customer ticket here...")

    if st.button("Analyze Ticket"):
        graph = build_graph()
        result = graph.invoke({"ticket": ticket})

        # ----- DECISION UI -----
        st.subheader("📊 Decision")
        urgency_color = {"low":"🟢 Low","medium":"🟡 Medium","high":"🔴 High"}
        sentiment_icon = {"calm":"😌 Calm","neutral":"😐 Neutral","angry":"😠 Angry"}
        st.markdown(f"**Urgency:** {urgency_color.get(result.get('urgency','low'))}")
        st.markdown(f"**Category:** 🏷️ `{result.get('category','Other').capitalize()}`")
        st.markdown(f"**Customer Mood:** {sentiment_icon.get(result.get('sentiment','neutral'))}")
        st.markdown("**Confidence**")
        st.progress(int(result.get("confidence",0) * 100))

        if result.get("confidence",0) < CONFIDENCE_THRESHOLD:
            st.warning("⚠️ Low confidence. Auto-escalation suggested.")
            result["escalate"] = True

        if result.get("escalate"):
            st.error("🚨 Escalation Required")
        else:
            st.success("✅ No Escalation Needed")

        st.subheader("✉️ Suggested Reply")
        st.write(result.get("suggested_reply","No suggestion available"))

        # ----- LOG TO SUPABASE -----
        supabase.table("support_audit_logs").insert({
            "user_id": st.session_state["user"]["id"],
            "ticket_text": ticket,
            "urgency": result.get("urgency"),
            "category": result.get("category"),
            "sentiment": result.get("sentiment"),
            "escalate": result.get("escalate"),
            "confidence": result.get("confidence")
        }).execute()

# ==================================================
# 📜 PAGE: Audit Logs
# ==================================================
if page == "Audit Logs":
    st.title("📜 Your Audit Logs")
    logs = (
        supabase
        .table("support_audit_logs")
        .select("*")
        .eq("user_id", st.session_state["user"]["id"])
        .order("created_at", desc=True)
        .execute()
        .data
    )

    if not logs:
        st.info("No logs yet.")
    else:
        for log in logs:
            with st.expander(f"🕒 {log.get('created_at','')} — {log.get('category','Other')}"):
                st.markdown(f"**Urgency:** {log.get('urgency','')}")
                st.markdown(f"**Sentiment:** {log.get('sentiment','')}")
                st.markdown(f"**Escalate:** {log.get('escalate',False)}")
                st.progress(int(log.get("confidence",0)*100))
                st.markdown("**Ticket:**")
                st.write(log.get("ticket_text",""))

        # CSV export
        df = pd.DataFrame(logs)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export CSV", csv, "audit_logs.csv", "text/csv")

# ==================================================
# 📈 PAGE: Manager Dashboard
# ==================================================
if page == "Manager Dashboard":
    manager_dashboard()

# ==================================================
# 📊 PAGE: Admin Dashboard
# ==================================================
if page == "Admin Dashboard":
    admin_dashboard()
