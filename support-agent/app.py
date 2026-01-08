import streamlit as st
from graph.workflow import build_graph
from utils.supabase_client import supabase
from utils.auth import login, signup, logout
from dashboards.admin import admin_dashboard
from dashboards.manager import manager_dashboard
import pandas as pd

# ---------------- CONFIG ----------------
CONFIDENCE_THRESHOLD = 0.6
st.set_page_config(page_title="AI Support Triage", layout="wide")
st.title("🎧 AI Support Triage Agent")

# ---------------- AUTH GATE ----------------
if "user" not in st.session_state:
    st.write("## 🔐 Please login or sign up")
    tab1, tab2 = st.tabs(["Login", "Sign up"])
    with tab1:
        login()
    with tab2:
        signup()
    st.stop()

# ---------------- LOGOUT ----------------
st.sidebar.button("Logout", on_click=logout)

# ---------------- NAVIGATION ----------------
page = st.sidebar.radio(
    "Navigation",
    ["Analyze Ticket", "Audit Logs", "Admin Dashboard", "Manager Dashboard", "Help"]
)

# ==================================================
# 📊 PAGE 1 — ANALYZE TICKET
# ==================================================
if page == "Analyze Ticket":
    st.subheader("Paste customer ticket here…")
    ticket = st.text_area("", placeholder="Customer complaint, email, or chat message…")

    if st.button("Analyze Ticket") and ticket.strip():
        graph = build_graph()
        result = graph.invoke({"ticket": ticket})

        # --------- DECISION UI ----------
        st.subheader("📊 Decision")
        urgency_color = {"low": "🟢 Low", "medium": "🟡 Medium", "high": "🔴 High"}
        sentiment_icon = {"calm": "😌 Calm", "neutral": "😐 Neutral", "angry": "😠 Angry"}

        urgency = result.get("urgency", "low")
        category = result.get("category", "Other")
        sentiment = result.get("sentiment", "neutral")
        escalate = result.get("escalate", False)
        confidence = result.get("confidence", 0)

        st.markdown(f"**Urgency:** {urgency_color.get(urgency,'🟢 Low')}")
        st.markdown(f"**Category:** 🏷️ `{category.capitalize()}`")
        st.markdown(f"**Customer Mood:** {sentiment_icon.get(sentiment,'😐 Neutral')}")
        st.markdown("**Confidence**")
        st.progress(int(confidence * 100))

        if confidence < CONFIDENCE_THRESHOLD:
            st.warning("⚠️ Low confidence. Manual review recommended.")
            escalate = True

        if escalate:
            st.error("🚨 Escalation Required")
        else:
            st.success("✅ No Escalation Needed")

        st.subheader("✉️ Suggested Reply")
        st.write(result.get("suggested_reply","Thanks for reaching out. We’ve received your request and our support team will review it shortly."))

        # --------- LOG TO SUPABASE (RLS-SAFE) ----------
        try:
            supabase.table("support_audit_logs").insert({
                "user_id": st.session_state["user"]["id"],  # must match auth.uid()
                "ticket_text": ticket,
                "urgency": urgency,
                "category": category,
                "sentiment": sentiment,
                "escalate": escalate,
                "confidence": confidence
            }).execute()
            st.success("✅ Ticket logged successfully")
        except Exception as e:
            st.error(f"❌ Failed to log ticket: {e}")

# ==================================================
# 📜 PAGE 2 — AUDIT LOGS
# ==================================================
if page == "Audit Logs":
    st.subheader("📜 Your Audit Logs")
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
                st.progress(int(log.get("confidence",0) * 100))
                st.markdown("**Ticket:**")
                st.write(log.get("ticket_text",""))

        # Export CSV
        df = pd.DataFrame(logs)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Export CSV",
            csv,
            "audit_logs.csv",
            "text/csv"
        )

# ==================================================
# 🛠 PAGE 3 — ADMIN DASHBOARD
# ==================================================
if page == "Admin Dashboard":
    admin_dashboard()  # your colorful charts, escalations, trends, Stripe integration

# ==================================================
# 🏢 PAGE 4 — MANAGER DASHBOARD
# ==================================================
if page == "Manager Dashboard":
    manager_dashboard()  # aggregate views, team stats, approvals

# ==================================================
# ❓ PAGE 5 — HELP
# ==================================================
if page == "Help":
    st.subheader("📌 How to use AI Support Triage")
    st.markdown("""
    1. Go to 'Analyze Ticket' and paste customer messages.
    2. Check the AI's urgency, sentiment, and suggested reply.
    3. Low confidence triggers manual review.
    4. All tickets are logged automatically.
    5. Admins can see trends, escalations, and Stripe billing.
    """)
