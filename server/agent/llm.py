from langchain_google_genai import ChatGoogleGenerativeAI

from server.config import settings


def get_llm(temperature: float = 0.2, model: str = "gemini-2.5-flash") -> ChatGoogleGenerativeAI:
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=settings.GOOGLE_API_KEY,
        temperature=temperature,
    )
