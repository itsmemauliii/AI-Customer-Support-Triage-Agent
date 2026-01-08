import streamlit as st
import pandas as pd

from graph.workflow import build_graph
from utils.supabase_client import supabase
from utils.auth import login, signup, logout

# ---------------- CONFIG ----------------
st.set_page_config(
    page_title="AI Support Triage",
    layout="wide"
)

CONFIDENCE_THRESHOLD = 0.6

st.title("🎧 AI Support Triage Agent")

# ---------------- AUTH GATE ----------------
if "user" not in st.session_state:
    st.subheader("🔐 Login to continue")

    tab1, tab2 = st.tabs(["Login", "Sign up"])
    with tab1:
        login()
    with tab2:
        signup()

    st.stop()

# ---------------- LOGOUT ----------------
logout()  # sidebar button

# ---------------- NAVIGATION ----------------
page = st.sidebar.radio(
    "🎛️ Control Panel",
    [
        "Analyze Ticket",
        "Audit Logs",
        "Escalations",
        "Insights",
        "Settings"
    ]
)

# ==================================================
# 📊 ANALYZE TICKET
# ==================================================
if page == "Analyze Ticket":
    st.subheader("📩 New Support Ticket")

    ticket = st.text_area(
        "Paste customer ticket",
        placeholder="Customer complaint, email, or chat message here…"
    )

    if st.button("🚀 Analyze Ticket", use_container_width=True):
        if not ticket.strip():
            st.warning("Please paste a ticket first.")
            st.stop()

        graph = build_graph()
        result = graph.invoke({"ticket": ticket})

        # -------- DEBUG (REMOVE LATER) ----------
        # st.json(result)

        # -------- SAFETY FIXES ----------
        urgency = result.get("urgency", "medium").lower()
        if urgency not in ["low", "medium", "high"]:
            urgency = "medium"

        sentiment = result.get("sentiment", "neutral").lower()
        confidence = float(result.get("confidence", 0.5))
        escalate = bool(result.get("escalate", False))

        # -------- CONFIDENCE RULE ----------
        if confidence < CONFIDENCE_THRESHOLD:
            escalate = True

        # -------- DECISION UI ----------
        st.divider()
        st.subheader("📊 Decision")

        urgency_badge = {
            "low": "🟢 Low",
            "medium": "🟡 Medium",
            "high": "🔴 High"
        }

        sentiment_badge = {
            "calm": "😌 Calm",
            "neutral": "😐 Neutral",
            "angry": "😠 Angry"
        }

        col1, col2, col3 = st.columns(3)
        col1.metric("Urgency", urgency_badge[urgency])
        col2.metric("Sentiment", sentiment_badge.get(sentiment, "😐 Neutral"))
        col3.metric("Confidence", f"{int(confidence * 100)}%")

        st.progress(int(confidence * 100))

        if escalate:
            st.error("🚨 Escalation Required")
        else:
            st.success("✅ No Escalation Needed")

        # -------- SUGGESTED REPLY ----------
        st.subheader("✉️ Suggested Reply")
        st.write(result.get("suggested_reply", "Thanks for reaching out. We’ll review this shortly."))

        # -------- LOG TO SUPABASE ----------
        supabase.table("support_audit_logs").insert({
            "user_id": st.session_state["user"]["id"],
            "ticket_text": ticket,
            "urgency": urgency,
            "category": result.get("category", "other"),
            "sentiment": sentiment,
            "escalate": escalate,
            "confidence": confidence
        }).execute()

# ==================================================
# 📜 AUDIT LOGS
# ==================================================
elif page == "Audit Logs":
    st.subheader("📜 Audit Logs")

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
        df = pd.DataFrame(logs)

        for log in logs:
            with st.expander(f"🕒 {log['created_at']} — {log['category']}"):
                st.write(log["ticket_text"])
                st.markdown(f"**Urgency:** {log['urgency']}")
                st.markdown(f"**Sentiment:** {log['sentiment']}")
                st.markdown(f"**Escalate:** {log['escalate']}")
                st.progress(int(log["confidence"] * 100))

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Export CSV",
            csv,
            "audit_logs.csv",
            "text/csv"
        )

# ==================================================
# 🚨 ESCALATIONS
# ==================================================
elif page == "Escalations":
    st.subheader("🚨 Escalated Tickets")

    rows = (
        supabase
        .table("support_audit_logs")
        .select("*")
        .eq("escalate", True)
        .order("created_at", desc=True)
        .execute()
        .data
    )

    if not rows:
        st.success("No escalations 🎉")
    else:
        for r in rows:
            with st.expander(f"🔥 {r['urgency'].upper()} — {r['category']}"):
                st.write(r["ticket_text"])
                st.progress(int(r["confidence"] * 100))

# ==================================================
# 📈 INSIGHTS
# ==================================================
elif page == "Insights":
    st.subheader("📈 Support Insights")

    data = (
        supabase
        .table("support_audit_logs")
        .select("urgency, sentiment, escalate")
        .execute()
        .data
    )

    if not data:
        st.info("No data yet.")
    else:
        df = pd.DataFrame(data)

        col1, col2, col3 = st.columns(3)
        col1.metric("Total Tickets", len(df))
        col2.metric("High Urgency", len(df[df.urgency == "high"]))
        col3.metric(
            "Escalation Rate",
            f"{round(df.escalate.mean() * 100, 1)}%"
        )

# ==================================================
# ⚙️ SETTINGS
# ==================================================
elif page == "Settings":
    st.subheader("⚙️ Settings")
    st.info("More controls coming soon 👀")
