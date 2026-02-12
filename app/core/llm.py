import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
# Use the newer integration for better stability
try:
    from langchain_ollama import ChatOllama
except ImportError:
    from langchain_community.chat_models import ChatOllama

from app.core.config import config

def get_llm(temperature=None, provider="gemini", model_name=None):
    """
    Factory function to get the LLM instance.
    
    Args:
        temperature (float): Creativity (0.0 to 1.0).
        provider (str): "gemini", "ollama", or "groq".
        model_name (str): Optional override (e.g., "gemma3:1b").
    """
    final_temp = temperature if temperature is not None else config.GEMINI_TEMPERATURE

    # --- OPTION 1: GROQ (Fastest / Recommended for Logic) ---
    if provider == "groq":
        # Default to a fast, smart model like Llama 3.1 8B
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

    # --- OPTION 2: OLLAMA (Local / Privacy / Free) ---
    if provider == "ollama":
        # Defaults to "gemma3:1b" if not specified, based on your request
        selected_model = model_name if model_name else "gemma3:1b"
        
        return ChatOllama(
            model=selected_model,
            temperature=final_temp,
            # Point to your local Ollama instance (default port 11434)
            base_url=getattr(config, 'OLLAMA_BASE_URL', "http://localhost:11434"),
            # Optional: Extend timeout for local hardware if needed
            timeout=120.0 
        )

    # --- OPTION 3: GEMINI (Default / Best for Vision) ---
    if provider == "gemini":
        if not config.GEMINI_API_KEY:
            raise ValueError("GEMINI_API_KEY is not set in the environment variables.")

        return ChatGoogleGenerativeAI(
            model=config.GEMINI_MODEL,
            temperature=final_temp,
            google_api_key=config.GEMINI_API_KEY,
            convert_system_message_to_human=True,
            request_timeout=60
        )
    
    raise ValueError(f"Unknown provider: {provider}")