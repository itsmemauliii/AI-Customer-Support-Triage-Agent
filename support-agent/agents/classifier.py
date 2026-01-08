def classify_ticket(state):
    text = state["ticket"].lower()

    if "refund" in text or "charge" in text:
        state["category"] = "billing"
        state["urgency"] = "high"
        state["sentiment"] = "angry"
        state["escalate"] = True
    elif "login" in text or "password" in text:
        state["category"] = "login"
        state["urgency"] = "medium"
        state["sentiment"] = "neutral"
        state["escalate"] = False
    else:
        state["category"] = "other"
        state["urgency"] = "low"
        state["sentiment"] = "calm"
        state["escalate"] = False

    return state
