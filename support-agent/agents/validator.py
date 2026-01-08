import json
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)


def validate_decision(state):
    prompt = open("prompts/validate.txt").read()

    response = llm.invoke(
        f"{prompt}\n\nCurrent decision:\n{state}"
    )

    validated = json.loads(response.content)
    state.update(validated)

    return state
