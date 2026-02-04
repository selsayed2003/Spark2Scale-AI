from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import config

def get_llm(temperature=None):
    """
    Factory function to get the LLM instance.
    """
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in the environment variables.")
    
    final_temp = temperature if temperature is not None else config.GEMINI_TEMPERATURE

    return ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        temperature=final_temp,
        google_api_key=config.GEMINI_API_KEY,
        convert_system_message_to_human=True
    )
