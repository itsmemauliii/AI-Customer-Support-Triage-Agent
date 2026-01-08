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
st.markdown("<style> .sidebar .sidebar-content {background-color:#ff4b4b;} </style>", unsafe_allow_html=True)

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
tabs = ["Analyze Ticket", "Audit Logs", "Manager Dashboard", "Admin Dashboard", "Settings"]
page = st.sidebar.radio("Navigate", tabs)

# ==================================================
# 📊 PAGE 1 — ANALYZE TICKET
# ==================================================
if page == "Analyze Ticket":
    st.subheader("📥 Paste Customer Ticket")
    ticket = st.text_area("Customer complaint, email, or chat message here…")

    if st.button("Analyze Ticket") and ticket.strip():
        graph = build_graph()
        result = graph.invoke({"ticket": ticket})

        # --------- DECISION UI ----------
        st.subheader("📊 Decision")

        urgency_color = {
            "low": "🟢 Low",
            "medium": "🟡 Medium",
            "high": "🔴 High"
        }
        st.markdown(f"**Urgency:** {urgency_color.get(result.get('urgency','low'))}")

        st.markdown(f"**Category:** 🏷️ `{result.get('category','Other').capitalize()}`")

        sentiment_icon = {
            "calm": "😌 Calm",
            "neutral": "😐 Neutral",
            "angry": "😠 Angry"
        }
        st.markdown(f"**Customer Mood:** {sentiment_icon.get(result.get('sentiment','neutral'))}")

        # --------- CONFIDENCE ----------
        confidence = result.get("confidence", 0)
        st.markdown("**Confidence**")
        st.progress(int(confidence * 100))

        if confidence < CONFIDENCE_THRESHOLD:
            st.warning("⚠️ Low confidence. Auto-escalation suggested.")
            result["escalate"] = True

        if result.get("escalate"):
            st.error("🚨 Escalation Required")
        else:
            st.success("✅ No Escalation Needed")

        st.subheader("✉️ Suggested Reply")
        st.write(result.get("suggested_reply", "No suggestion available"))

        # --------- LOG TO SUPABASE (RLS friendly) ----------
        try:
            supabase.table("support_audit_logs").insert({
                "user_id": st.session_state["user"]["id"],  # Must match auth.uid()
                "ticket_text": ticket,
                "urgency": result.get("urgency"),
                "category": result.get("category"),
                "sentiment": result.get("sentiment"),
                "escalate": result.get("escalate"),
                "confidence": result.get("confidence")
            }).execute()
            st.success("✅ Ticket logged successfully!")
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

        # CSV Export
        df = pd.DataFrame(logs)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export CSV", csv, "audit_logs.csv", "text/csv")

# ==================================================
# 📈 PAGE 3 — MANAGER DASHBOARD
# ==================================================
elif page == "Manager Dashboard":
    manager_dashboard()  # Implement charts, trends, escalations

# ==================================================
# 🛠️ PAGE 4 — ADMIN DASHBOARD
# ==================================================
elif page == "Admin Dashboard":
    admin_dashboard()  # Implement counts, user management, SaaS controls

# ==================================================
# ⚙️ PAGE 5 — SETTINGS
# ==================================================
elif page == "Settings":
    st.title("⚙️ Settings & Billing")
    st.write("Add Stripe billing integration here and other SaaS configs")
