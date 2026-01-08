import streamlit as st
from graph.workflow import build_graph

st.set_page_config(page_title="AI Support Triage Agent")

st.title("🧠 AI Customer Support Triage Agent")

ticket = st.text_area("Paste support ticket", height=200)
plan = st.selectbox("Customer plan", ["Free", "Paid", "Enterprise"])

if st.button("Analyze Ticket"):
    if not ticket.strip():
        st.warning("Please enter a ticket.")
    else:
        graph = build_graph()

        state = {
            "ticket": ticket,
            "plan": plan
        }

        result = graph.invoke(state)

        st.subheader("📊 Decision")
        st.subheader("📊 Decision")

# Urgency badge
urgency_color = {
    "low": "🟢 Low",
    "medium": "🟡 Medium",
    "high": "🔴 High"
}
st.markdown(f"**Urgency:** {urgency_color[result['urgency']]}")

# Category
st.markdown(f"**Category:** 🏷️ `{result['category'].capitalize()}`")

# Sentiment
sentiment_icon = {
    "calm": "😌 Calm",
    "neutral": "😐 Neutral",
    "angry": "😠 Angry"
}
st.markdown(f"**Customer Mood:** {sentiment_icon[result['sentiment']]}")

# Escalation button
if result["escalate"]:
    st.error("🚨 Escalation Required")
else:
    st.success("✅ No Escalation Needed")

# Confidence bar
st.markdown("**Confidence**")
st.progress(int(result["confidence"] * 100))
st.subheader("✉️ Suggested Reply")
st.write(result["suggested_reply"])
