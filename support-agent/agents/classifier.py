import json
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def classify_ticket(state):
    ticket = state["ticket"]

    prompt = open("prompts/classify.txt").read()

    response = llm.invoke(
        f"{prompt}\n\nTicket:\n{ticket}"
    )

    data = json.loads(response.content)

    state.update(data)
    return state
