from langgraph.graph import StateGraph
from agents.classifier import classify_ticket
from agents.validator import validate_decision
from agents.responder import generate_reply
from agents.decider import final_decision


def build_graph():
    graph = StateGraph(dict)

    graph.add_node("classify", classify_ticket)
    graph.add_node("validate", validate_decision)
    graph.add_node("reply", generate_reply)
    graph.add_node("decide", final_decision)

    graph.set_entry_point("classify")

    graph.add_edge("classify", "validate")
    graph.add_edge("validate", "reply")
    graph.add_edge("reply", "decide")

    graph.set_finish_point("decide")

    return graph.compile()
