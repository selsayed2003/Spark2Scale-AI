from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os

load_dotenv()

class Settings(BaseSettings):
    OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
    TAVILY_API_KEY: str = os.getenv("TAVILY_API_KEY", "")
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "")
    SERPER_API_KEY: str = os.getenv("SERPER_API_KEY", "")
    GEMINI_MODEL_NAME: str = "gemini-2.5-flash-lite"

    class Config:
        env_file = ".env"
        extra = "ignore"

settings = Settings()

from google import genai
try:
    gemini_client = genai.Client(api_key=settings.GEMINI_API_KEY)
except Exception as e:
    print(f"Warning: Failed to initialize Gemini client: {e}")
    gemini_client = None
