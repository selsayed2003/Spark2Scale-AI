import os
from langchain_google_genai import ChatGoogleGenerativeAI
from app.core.config import config

def get_llm(temperature=None, provider="gemini", model_name=None):
    """
    Factory function to get the LLM instance.
    
    Args:
        temperature (float): Creativity (0.0 to 1.0).
        provider (str): "gemini", "ollama", or "groq".
        model_name (str): Optional override.
    """
    final_temp = temperature if temperature is not None else config.GEMINI_TEMPERATURE

    # --- GROQ ---
    if provider == "groq":
        try:
            from langchain_groq import ChatGroq
        except ImportError:
            raise ValueError("Groq provider not available. Install: pip install langchain-groq")
        
        selected_model = model_name if model_name else "llama-3.1-8b-instant"
        api_key = os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise ValueError("GROQ_API_KEY is not set.")
        
        return ChatGroq(
            temperature=final_temp,
            model_name=selected_model,
            api_key=api_key,
            max_retries=2,
            request_timeout=30 
        )

    # --- OLLAMA ---
    if provider == "ollama":
        try:
            from langchain_community.chat_models import ChatOllama
        except ImportError:
            raise ValueError("Ollama provider not available. Install: pip install langchain-community")
        
        selected_model = model_name if model_name else "llama3"
        return ChatOllama(
            model=selected_model,
            format="json", 
            temperature=final_temp,
            base_url=getattr(config, 'OLLAMA_BASE_URL', "http://localhost:11434")
        )

    # --- GEMINI (Default) ---
    if not config.GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in the environment variables.")

    return ChatGoogleGenerativeAI(
        model=config.GEMINI_MODEL,
        temperature=final_temp,
        google_api_key=config.GEMINI_API_KEY,
        convert_system_message_to_human=True,
        request_timeout=60
    )