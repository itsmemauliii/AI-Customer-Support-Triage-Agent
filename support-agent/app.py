import streamlit as st
import pandas as pd
import random
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
st.sidebar.button("Logout", on_click=logout)

# ---------------- NAVIGATION ----------------
page = st.sidebar.radio(
    "Navigate",
    ["Analyze Ticket", "Audit Logs", "Admin Dashboard", "Manager Dashboard", "Help"]
)

# ---------------- SIMPLE AI CLASSIFIER ----------------
def simple_ai_classify(ticket_text):
    ticket_text_lower = ticket_text.lower()
    if any(x in ticket_text_lower for x in ["urgent", "immediately", "cancel", "payment", "lost", "error"]):
        urgency = "high"
        sentiment = "angry"
        escalate = True
    elif any(x in ticket_text_lower for x in ["problem", "issue", "delay"]):
        urgency = "medium"
        sentiment = "neutral"
        escalate = False
    else:
        urgency = "low"
        sentiment = "calm"
        escalate = False

    confidence = random.uniform(0.7, 0.99)
    category = "billing" if "payment" in ticket_text_lower else "other"
    return {
        "urgency": urgency,
        "category": category,
        "sentiment": sentiment,
        "escalate": escalate,
        "confidence": confidence,
        "suggested_reply": "Thanks for reaching out. We’ve received your request and our support team will review it shortly."
    }

# ==================================================
# 📊 PAGE 1 — ANALYZE TICKET
# ==================================================
if page == "Analyze Ticket":
    ticket = st.text_area("Paste customer ticket here…", height=150)

    if st.button("Analyze Ticket"):
        if not ticket.strip():
            st.warning("⚠️ Please enter a ticket to analyze.")
        else:
            result = simple_ai_classify(ticket)

            # --------- DECISION UI ----------
            st.subheader("📊 Decision")
            urgency_color = {"low": "🟢 Low", "medium": "🟡 Medium", "high": "🔴 High"}
            sentiment_icon = {"calm": "😌 Calm", "neutral": "😐 Neutral", "angry": "😠 Angry"}

            st.markdown(f"**Urgency:** {urgency_color[result['urgency']]}")
            st.markdown(f"**Category:** 🏷️ `{result['category'].capitalize()}`")
            st.markdown(f"**Customer Mood:** {sentiment_icon[result['sentiment']]}")

            # --------- CONFIDENCE ----------
            st.markdown("**Confidence**")
            st.progress(int(result["confidence"] * 100))

            # --------- CONFIDENCE WARNING ----------
            if result["confidence"] < CONFIDENCE_THRESHOLD:
                st.warning("⚠️ Low confidence. Manual review recommended.")

            # --------- ESCALATION ----------
            if result["escalate"]:
                st.error("🚨 Escalation Required")
            else:
                st.success("✅ No Escalation Needed")

            # --------- SUGGESTED REPLY ----------
            st.subheader("✉️ Suggested Reply")
            st.write(result["suggested_reply"])

            # --------- LOG TO SUPABASE (AFTER UI) ----------
            try:
                supabase.table("support_audit_logs").insert({
                    "user_id": st.session_state["user"]["id"],  # Must match auth.uid()
                    "ticket_text": ticket,
                    "urgency": result["urgency"],
                    "category": result["category"],
                    "sentiment": result["sentiment"],
                    "escalate": result["escalate"],
                    "confidence": result["confidence"]
                }).execute()
            except Exception as e:
                st.error(f"❌ Failed to log ticket: {e}")

# ==================================================
# 📜 PAGE 2 — AUDIT LOGS
# ==================================================
if page == "Audit Logs":
    st.title("📜 Audit Logs")
    try:
        logs = (
            supabase.table("support_audit_logs")
            .select("*")
            .eq("user_id", st.session_state["user"]["id"])
            .order("created_at", desc=True)
            .execute()
            .data
        )
    except Exception as e:
        st.error(f"❌ Failed to fetch logs: {e}")
        logs = []

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
        st.download_button("⬇️ Export CSV", csv, "audit_logs.csv", "text/csv")

# ==================================================
# 🛠️ PAGE 3 — ADMIN DASHBOARD
# ==================================================
if page == "Admin Dashboard":
    admin_dashboard()

# ==================================================
# 📊 PAGE 4 — MANAGER DASHBOARD
# ==================================================
if page == "Manager Dashboard":
    manager_dashboard()

# ==================================================
# ❓ PAGE 5 — HELP
# ==================================================
if page == "Help":
    st.title("💡 Help & Instructions")
    st.markdown("""
    - Navigate using the sidebar.
    - Paste customer tickets to analyze them.
    - Admins can view all logs and trends.
    - Managers can monitor escalations.
    """)
