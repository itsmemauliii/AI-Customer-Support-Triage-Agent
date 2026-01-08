import streamlit as st
from graph.workflow import build_graph

st.title("🎧 AI Support Triage Agent")

ticket = st.text_area("Paste customer ticket")

if st.button("Analyze Ticket"):
    graph = build_graph()

    result = graph.invoke({
        "ticket": ticket
    })

    # ---- UI STARTS HERE (result EXISTS now) ----
    st.subheader("📊 Decision")

    urgency_color = {
        "low": "🟢 Low",
        "medium": "🟡 Medium",
        "high": "🔴 High"
    }
    st.markdown(f"**Urgency:** {urgency_color[result['urgency']]}")

    st.markdown(f"**Category:** 🏷️ `{result['category'].capitalize()}`")

    sentiment_icon = {
        "calm": "😌 Calm",
        "neutral": "😐 Neutral",
        "angry": "😠 Angry"
    }
    st.markdown(f"**Customer Mood:** {sentiment_icon[result['sentiment']]}")

    if result["escalate"]:
        st.error("🚨 Escalation Required")
    else:
        st.success("✅ No Escalation Needed")

    st.markdown("**Confidence**")
    st.progress(int(result["confidence"] * 100))

    st.subheader("✉️ Suggested Reply")
    st.write(result["suggested_reply"])
