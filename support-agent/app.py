import streamlit as st
from graph.workflow import build_graph
from utils.supabase_client import supabase
from utils.auth import login, signup, logout
from dashboards.admin import admin_dashboard
if page == "Admin Dashboard":
    admin_dashboard()
# ---------------- CONFIG ----------------
CONFIDENCE_THRESHOLD = 0.6
st.set_page_config(page_title="AI Support Triage", layout="centered")
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
logout()  # sidebar logout button

# ---------------- NAVIGATION ----------------
page = st.sidebar.radio(
    "Navigation",
    ["Analyze Ticket", "Audit Logs"]
)

# ==================================================
# 📊 PAGE 1 — ANALYZE TICKET
# ==================================================
if page == "Analyze Ticket":
    ticket = st.text_area("Paste customer ticket")

    if st.button("Analyze Ticket"):
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

        # --------- CONFIDENCE WARNING ----------
        if confidence < CONFIDENCE_THRESHOLD:
            st.warning("⚠️ Low confidence. Auto-escalation suggested.")
            result["escalate"] = True

        # --------- ESCALATION ----------
        if result.get("escalate"):
            st.error("🚨 Escalation Required")
        else:
            st.success("✅ No Escalation Needed")

        # --------- SUGGESTED REPLY ----------
        st.subheader("✉️ Suggested Reply")
        st.write(result.get("suggested_reply","No suggestion available"))

        # --------- LOG TO SUPABASE (AFTER UI) ----------
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
# 📜 PAGE 2 — AUDIT LOGS
# ==================================================
if page == "Audit Logs":
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
                st.progress(int(log.get("confidence",0) * 100))
                st.markdown("**Ticket:**")
                st.write(log.get("ticket_text",""))
