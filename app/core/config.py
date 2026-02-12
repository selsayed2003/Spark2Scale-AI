import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-flash-latest")
    GEMINI_TEMPERATURE = float(os.getenv("GEMINI_TEMPERATURE", "0.7"))
    MAX_ITERATIONS = int(os.getenv("MAX_ITERATIONS", "2"))
    POLLINATIONS_API_KEY = os.getenv("POLLINATIONS_API_KEY")
    # Image generation: "flux" (default), "gptimage", "gptimage-large", "seedream", "seedream-pro". gptimage-large often better for simple icons.
    IMAGE_MODEL = os.getenv("IMAGE_MODEL", "klein")
    # Optional: use OpenAI DALL-E 3 for images (set OPENAI_API_KEY and IMAGE_PROVIDER=openai)
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    IMAGE_PROVIDER = os.getenv("IMAGE_PROVIDER", "pollinations")  # "pollinations" | "openai"


config = Config()
