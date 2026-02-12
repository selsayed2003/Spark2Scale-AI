import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "2"))
    POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
    # Image generation:
    # - Provider is configured via IMAGE_PROVIDER: "pollinations" (default) or "google" (Gemini image model).
    # - IMAGE_MODEL controls the underlying model name for that provider.
    IMAGE_MODEL = os.getenv("IMAGE_MODEL", "gptimage-large")
    IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "pollinations")  # "pollinations" | "google"


config = Config()
