from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.3)


def generate_reply(state):
    prompt = open("prompts/reply.txt").read()

    response = llm.invoke(
        f"{prompt}\n\nTicket:\n{state['ticket']}"
    )

    state["suggested_reply"] = response.content
    return state
