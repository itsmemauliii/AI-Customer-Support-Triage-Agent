def final_decision(state):
    # Add confidence heuristics
    confidence = 0.9

    if state["urgency"] == "low":
        confidence = 0.95
    elif state["urgency"] == "high":
        confidence = 0.85

    state["confidence"] = confidence

    return state
