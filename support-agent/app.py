import streamlit as st
from graph.workflow import build_graph
from utils.supabase_client import supabase
from utils.auth import login, signup, logout
from utils.roles import is_admin, is_manager
from dashboards.admin import admin_dashboard
from dashboards.manager import manager_dashboard

CONFIDENCE_THRESHOLD = 0.6

st.set_page_config(
    page_title="AI Support Triage",
    page_icon="🎧",
    layout="wide"
)

# ------------------------------------------------
# AUTH GATE
# ------------------------------------------------
if "user" not in st.session_state:
    st.markdown("## 🔐 Welcome to AI Support Triage")
    tab1, tab2 = st.tabs(["Login", "Sign up"])
    with tab1:
        login()
    with tab2:
        signup()
    st.stop()

user = st.session_state["user"]

# ------------------------------------------------
# SIDEBAR (ROLE BASED)
# ------------------------------------------------
st.sidebar.markdown("### 🎛️ Control Panel")

pages = ["Analyze Ticket", "Audit Logs"]

if is_manager(user):
    pages.append("Manager Dashboard")

if is_admin(user):
    pages.append("Admin Dashboard")

page = st.sidebar.radio("Navigate", pages)

st.sidebar.divider()
logout()

# ------------------------------------------------
# ANALYZE TICKET (AGENTS)
# ------------------------------------------------
if page == "Analyze Ticket":
    st.title("🎧 AI Support Triage")

    ticket = st.text_area(
        "Paste customer ticket",
        placeholder="Customer complaint, email, or chat message here…"
    )

    if st.button("🚀 Analyze Ticket", use_container_width=True):
        graph = build_graph()
        result = graph.invoke({"ticket": ticket})

        st.subheader("📊 Decision")

        urgency_map = {
            "low": "🟢 Low",
            "medium": "🟡 Medium",
            "high": "🔴 High"
        }
        st.markdown(f"**Urgency:** {urgency_map.get(result['urgency'])}")
        st.markdown(f"**Category:** 🏷️ `{result['category'].title()}`")

        mood_map = {
            "calm": "😌 Calm",
            "neutral": "😐 Neutral",
            "angry": "😠 Angry"
        }
        st.markdown(f"**Customer Mood:** {mood_map.get(result['sentiment'])}")

        confidence = result["confidence"]
        st.markdown("**Confidence**")
        st.progress(int(confidence * 100))

        if confidence < CONFIDENCE_THRESHOLD:
            st.warning("⚠️ Low confidence — escalation recommended")
            result["escalate"] = True

        if result["escalate"]:
            st.error("🚨 Escalation Required")
        else:
            st.success("✅ No Escalation Needed")

        st.subheader("✉️ Suggested Reply")
        st.write(result["suggested_reply"])

        # LOG AFTER UI
        supabase.table("support_audit_logs").insert({
            "user_id": user["id"],
            "ticket_text": ticket,
            "urgency": result["urgency"],
            "category": result["category"],
            "sentiment": result["sentiment"],
            "escalate": result["escalate"],
            "confidence": result["confidence"]
        }).execute()

# ------------------------------------------------
# AUDIT LOGS (AGENTS)
# ------------------------------------------------
if page == "Audit Logs":
    st.title("📜 Your Audit Logs")

    logs = (
        supabase
        .table("support_audit_logs")
        .select("*")
        .eq("user_id", user["id"])
        .order("created_at", desc=True)
        .execute()
        .data
    )

    if not logs:
        st.info("No tickets analyzed yet.")
    else:
        for log in logs:
            with st.expander(f"🕒 {log['created_at']} — {log['category']}"):
                st.markdown(f"**Urgency:** {log['urgency']}")
                st.markdown(f"**Sentiment:** {log['sentiment']}")
