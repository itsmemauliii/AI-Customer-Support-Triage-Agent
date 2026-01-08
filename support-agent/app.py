import streamlit as st
import pandas as pd
from graph.workflow import build_graph
from utils.supabase_client import supabase
from utils.auth import login, signup, logout
from dashboards.admin import admin_dashboard
from dashboards.manager import manager_dashboard

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
with st.sidebar:
    if st.button("Logout"):
        logout()
        st.experimental_rerun()

# ---------------- NAVIGATION ----------------
pages = ["Analyze Ticket", "Audit Logs", "Admin Dashboard", "Manager Dashboard", "Help"]
page = st.sidebar.radio("Navigate", pages)

# ==================================================
# 📊 PAGE 1 — ANALYZE TICKET
# ==================================================
if page == "Analyze Ticket":
    ticket = st.text_area("Paste customer ticket here…")

    if st.button("Analyze Ticket") and ticket.strip():
        graph = build_graph()
        result = graph.invoke({"ticket": ticket})

        # --------- DECISION UI ----------
        st.subheader("📊 Decision")
        urgency_color = {"low": "🟢 Low", "medium": "🟡 Medium", "high": "🔴 High"}
        st.markdown(f"**Urgency:** {urgency_color.get(result.get('urgency','low'))}")
        st.markdown(f"**Category:** 🏷️ {result.get('category','Other').capitalize()}")
        sentiment_icon = {"calm": "😌 Calm", "neutral": "😐 Neutral", "angry": "😠 Angry"}
        st.markdown(f"**Customer Mood:** {sentiment_icon.get(result.get('sentiment','neutral'))}")

        # --------- CONFIDENCE ----------
        confidence = result.get("confidence", 0)
        st.markdown("**Confidence**")
        st.progress(int(confidence * 100))

        # --------- CONFIDENCE WARNING ----------
        escalate = result.get("escalate", False)
        if confidence < CONFIDENCE_THRESHOLD:
            st.warning("⚠️ Low confidence. Auto-escalation suggested.")
            escalate = True

        # --------- ESCALATION ----------
        if escalate:
            st.error("🚨 Escalation Required")
        else:
            st.success("✅ No Escalation Needed")

        # --------- SUGGESTED REPLY ----------
        st.subheader("✉️ Suggested Reply")
        st.write(result.get("suggested_reply","No suggestion available"))

        # --------- LOG TO SUPABASE ----------
        try:
            supabase.table("support_audit_logs").insert({
                "user_id": st.session_state["user"]["id"],  # must match auth.uid()
                "ticket_text": ticket,
                "urgency": result.get("urgency"),
                "category": result.get("category"),
                "sentiment": result.get("sentiment"),
                "escalate": escalate,
                "confidence": confidence
            }).execute()
        except Exception as e:
            st.error(f"❌ Failed to log ticket: {e}")

# ==================================================
# 📜 PAGE 2 — AUDIT LOGS
# ==================================================
elif page == "Audit Logs":
    st.title("📜 Audit Logs")
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
# 🛠️ PAGE 3 — ADMIN DASHBOARD
# ==================================================
elif page == "Admin Dashboard":
    admin_dashboard()

# ==================================================
# 📈 PAGE 4 — MANAGER DASHBOARD
# ==================================================
elif page == "Manager Dashboard":
    manager_dashboard()

# ==================================================
# ❓ PAGE 5 — HELP / INFO
# ==================================================
elif page == "Help":
    st.title("💡 Help & Info")
    st.markdown("""
    - Paste a customer ticket in **Analyze Ticket**
    - Check your previous logs in **Audit Logs**
    - Admins can view counts and escalations in **Admin Dashboard**
    - Managers can view team trends in **Manager Dashboard**
    """)
