from langchain_anthropic import ChatAnthropic
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_google_genai import ChatGoogleGenerativeAI

_MESSAGE_TYPES = {"system": SystemMessage, "assistant": AIMessage}


def create_claude_client(temperature: float = 0.0) -> ChatAnthropic:
    return ChatAnthropic(model_name="claude-sonnet-4-5", temperature=temperature, timeout=None,
    stop=None)


def create_gemini_client(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=temperature)


def _to_langchain_messages(prompt: list[dict[str, str]]):
    return [_MESSAGE_TYPES.get(m["role"], HumanMessage)(content=m["content"]) for m in prompt]


def invoke_llm(client, prompt: list[dict[str, str]]) -> str:
    response = client.invoke(_to_langchain_messages(prompt))
    return _content_to_text(response.content)


def stream_llm(client, prompt: list[dict[str, str]]):
    for chunk in client.stream(_to_langchain_messages(prompt)):
        yield _content_to_text(chunk.content)


def _content_to_text(content) -> str:
    """Normalize LangChain provider content to the string API contract."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "".join(
            str(item.get("text") if isinstance(item, dict) else item)
            for item in content
            if (item.get("text") if isinstance(item, dict) else item)
        )
    return str(content) if content is not None else ""
