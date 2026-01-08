import streamlit as st
import pandas as pd
from graph.workflow import build_graph
from utils.supabase_client import supabase
from utils.auth import login, signup, logout
from dashboards.admin import admin_dashboard
from dashboards.manager import manager_dashboard

# ---------------- CONFIG ----------------
CONFIDENCE_THRESHOLD = 0.6
st.set_page_config(page_title="🎧 AI Support Triage", layout="wide", page_icon="🎧")

# ---------------- RED NAVIGATION ----------------
st.markdown(
    """
    <style>
    .css-1aumxhk {background-color:#ff4d4d !important;}  /* sidebar header red */
    .css-1d391kg {background-color:#ffcccc !important;}  /* sidebar background light red */
    </style>
    """, unsafe_allow_html=True
)

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
st.sidebar.button("🔒 Logout", on_click=logout)

# ---------------- NAVIGATION ----------------
tabs = ["Analyze Ticket", "Audit Logs", "Manager Dashboard", "Admin Dashboard", "Settings"]
page = st.sidebar.radio("Navigate", tabs)

# ---------------- SAMPLE TICKETS ----------------
sample_tickets = [
    "I haven't received my order yet and it's been 2 weeks!",
    "The app crashes every time I try to upload a file.",
    "I want to change my subscription plan but can't find the option.",
    "My payment failed and I need help resolving this.",
    "I received a damaged product, please advise."
]

# ==================================================
# 📊 PAGE 1 — ANALYZE TICKET
# ==================================================
if page == "Analyze Ticket":
    st.subheader("Paste Customer Ticket")
    ticket = st.text_area("Customer complaint, email, or chat message here…", value=sample_tickets[0])
    
    if st.button("Analyze Ticket"):
        graph = build_graph()
        result = graph.invoke({"ticket": ticket})

        # --------- DECISION UI ----------
        st.subheader("📊 Decision")
        urgency_color = {"low": "🟢 Low", "medium": "🟡 Medium", "high": "🔴 High"}
        st.markdown(f"**Urgency:** {urgency_color.get(result.get('urgency', 'low'))}")
        st.markdown(f"**Category:** 🏷️ `{result.get('category', 'Other').capitalize()}`")
        sentiment_icon = {"calm": "😌 Calm", "neutral": "😐 Neutral", "angry": "😠 Angry"}
        st.markdown(f"**Customer Mood:** {sentiment_icon.get(result.get('sentiment', 'neutral'))}")

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
        st.write(result.get("suggested_reply", "No suggestion available"))

        # --------- LOG TO SUPABASE (AFTER UI) ----------
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
            st.success("✅ Ticket logged successfully")
        except Exception as e:
            st.error(f"❌ Failed to log ticket: {e}")

# ==================================================
# 📜 PAGE 2 — AUDIT LOGS
# ==================================================
elif page == "Audit Logs":
    st.title("📜 Audit Logs")
    logs = (
        supabase.table("support_audit_logs")
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
            with st.expander(f"🕒 {log.get('created_at', '')} — {log.get('category', 'Other')}"):
                st.markdown(f"**Urgency:** {log.get('urgency','')}")
                st.markdown(f"**Sentiment:** {log.get('sentiment','')}")
                st.markdown(f"**Escalate:** {log.get('escalate', False)}")
                st.progress(int(log.get("confidence",0) * 100))
                st.markdown("**Ticket:**")
                st.write(log.get("ticket_text",""))

        # CSV Export
        df = pd.DataFrame(logs)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export CSV", csv, "audit_logs.csv", "text/csv")

# ==================================================
# 📊 PAGE 3 — MANAGER DASHBOARD
# ==================================================
elif page == "Manager Dashboard":
    manager_dashboard()

# ==================================================
# 📊 PAGE 4 — ADMIN DASHBOARD
# ==================================================
elif page == "Admin Dashboard":
    admin_dashboard()

# ==================================================
# 📊 PAGE 5 — SETTINGS (Future Stripe / Billing)
# ==================================================
elif page == "Settings":
    st.title("⚙️ Settings & Billing")
    st.info("Stripe billing integration and role management coming soon!")
