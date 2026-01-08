import streamlit as st
import pandas as pd
from graph.workflow import build_graph
from utils.supabase_client import supabase
from utils.auth import login, signup, logout
from dashboards.admin import admin_dashboard
from dashboards.manager import manager_dashboard

# ---------------- CONFIG ----------------
CONFIDENCE_THRESHOLD = 0.6
st.set_page_config(page_title="AI Support Triage", layout="centered")
st.markdown(
    """
    <style>
    /* Red sidebar */
    .css-1d391kg {background-color: #ff4b4b;}
    /* Sidebar text */
    .css-1d391kg .css-1o9y3b3 {color: white;}
    </style>
    """,
    unsafe_allow_html=True
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

# ---------------- LOGOUT BUTTON ----------------
st.sidebar.button("🚪 Logout", on_click=logout)

# ---------------- NAVIGATION ----------------
user_role = st.session_state["user"].get("role", "agent")  # agent or admin
pages = ["Analyze Ticket", "Audit Logs", "Sample Tickets", "Settings", "Help"]
if user_role == "admin":
    pages += ["Manager Dashboard", "Admin Dashboard"]

page = st.sidebar.radio("Navigate", pages)

# =========================
# 📊 PAGE 1 — ANALYZE TICKET
# =========================
if page == "Analyze Ticket":
    ticket = st.text_area("Paste customer ticket", placeholder="Customer complaint, email, or chat message…")

    if st.button("Analyze Ticket"):
        graph = build_graph()
        result = graph.invoke({"ticket": ticket})

        # --------- DECISION UI ----------
        urgency_color = {"low": "🟢 Low", "medium": "🟡 Medium", "high": "🔴 High"}
        sentiment_icon = {"calm": "😌 Calm", "neutral": "😐 Neutral", "angry": "😠 Angry"}

        urgency = str(result.get("urgency", "low")).strip().lower()
        sentiment = str(result.get("sentiment", "neutral")).strip().lower()
        confidence = float(result.get("confidence", 0))
        escalate = result.get("escalate", False)

        st.subheader("📊 Decision")
        st.markdown(f"**Urgency:** {urgency_color.get(urgency, '🟢 Low')}")
        st.markdown(f"**Category:** 🏷️ `{str(result.get('category','Other')).capitalize()}`")
        st.markdown(f"**Customer Mood:** {sentiment_icon.get(sentiment, '😐 Neutral')}")
        st.markdown("**Confidence**")
        st.progress(int(confidence * 100))

        if confidence < CONFIDENCE_THRESHOLD:
            st.warning("⚠️ Low confidence. Auto-escalation suggested.")
            escalate = True

        if escalate:
            st.error("🚨 Escalation Required")
        else:
            st.success("✅ No Escalation Needed")

        st.subheader("✉️ Suggested Reply")
        st.write(result.get("suggested_reply", "No suggestion available"))

        # --------- LOG TO SUPABASE (AFTER UI) ----------
        try:
            supabase.table("support_audit_logs").insert({
                "user_id": st.session_state["user"]["id"],
                "ticket_text": ticket,
                "urgency": urgency,
                "category": str(result.get("category","Other")).capitalize(),
                "sentiment": sentiment,
                "escalate": escalate,
                "confidence": confidence
            }).execute()
            st.success("✅ Ticket logged successfully")
        except Exception as e:
            st.error(f"❌ Failed to log ticket: {e}")

# =========================
# 📜 PAGE 2 — AUDIT LOGS
# =========================
elif page == "Audit Logs":
    st.title("📜 Audit Logs")

    try:
        logs = (
            supabase
            .table("support_audit_logs")
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

        # CSV export
        df = pd.DataFrame(logs)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export CSV", csv, "audit_logs.csv", "text/csv")

# =========================
# 📊 PAGE 3 — SAMPLE TICKETS
# =========================
elif page == "Sample Tickets":
    st.title("📝 Sample Tickets")
    sample_tickets = [
        "My internet has been down for 3 days. Please help!",
        "I received a damaged product and need a refund.",
        "The app keeps crashing whenever I try to login.",
        "I want to upgrade my plan to premium.",
        "I haven't received my order yet. Order #12345"
    ]
    for ticket in sample_tickets:
        st.write(f"- {ticket}")

# =========================
# 📊 PAGE 4 — SETTINGS
# =========================
elif page == "Settings":
    st.title("⚙️ Settings")
    st.write("Manage your preferences here (coming soon)")

# =========================
# 📊 PAGE 5 — HELP
# =========================
elif page == "Help":
    st.title("❓ Help")
    st.write("Contact support or read documentation (coming soon)")

# =========================
# 📊 PAGE 6 — MANAGER DASHBOARD
# =========================
elif page == "Manager Dashboard" and user_role == "admin":
    manager_dashboard()

# =========================
# 📊 PAGE 7 — ADMIN DASHBOARD
# =========================
elif page == "Admin Dashboard" and user_role == "admin":
    admin_dashboard()
