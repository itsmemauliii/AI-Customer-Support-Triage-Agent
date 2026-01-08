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
        st.json({
            "urgency": result["urgency"],
            "category": result["category"],
            "sentiment": result["sentiment"],
            "escalate": result["escalate"],
            "confidence": result["confidence"]
        })

        st.subheader("✉️ Suggested Reply")
        st.write(result["suggested_reply"])
