from langchain_anthropic import ChatAnthropic
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI


def create_claude_client(temperature: float = 0.0) -> ChatAnthropic:
    return ChatAnthropic(model="claude-sonnet-4-5", temperature=temperature)


def create_gemini_client(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=temperature)


def invoke_llm(client, prompt: list[dict[str, str]]) -> str:
    langchain_messages = [
        SystemMessage(content=m["content"])
        if m["role"] == "system"
        else HumanMessage(content=m["content"])
        for m in prompt
    ]
    response = client.invoke(langchain_messages)
    return response.content
