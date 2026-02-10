from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.chat_models import ChatOllama
from app.core.config import config

def get_llm(temperature=None, provider="gemini", model_name=None):
    """
    Factory function to get the LLM instance.
    
    Args:
        temperature (float): Creativity (0.0 to 1.0).
        provider (str): "gemini" or "ollama".
        model_name (str): Optional override (e.g., "gemma:2b").
    """
    final_temp = temperature if temperature is not None else config.GEMINI_TEMPERATURE

    if provider == "ollama":
        # Default to config model if not provided, or fallback to 'llama3'
        selected_model = model_name if model_name else "llama3"
        
        return ChatOllama(
            model=selected_model,
            format="json", # Crucial for structured output
            temperature=final_temp,
            base_url=config.OLLAMA_BASE_URL if hasattr(config, 'OLLAMA_BASE_URL') else "http://localhost:11434"
        )

    # Default to Gemini
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in the environment variables.")

    return ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        temperature=final_temp,
        google_api_key=config.GEMINI_API_KEY,
        convert_system_message_to_human=True
    )