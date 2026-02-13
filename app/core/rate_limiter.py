import time
import asyncio
import random
from app.core.config import Config, gemini_client
from app.graph.market_research_agent.logger_config import get_logger

logger = get_logger("RateLimiter")

class GeminiLimiter:
    _last_call_time = 0
    _min_interval = 2.0  # Increased to 6 seconds to be safe (10 requests/min = 1 req/6s)
                         # Wait, free tier is 15 RPM for Flash generally, but user saw 10 RPM message.
                         # 10 RPM = 1 request every 6 seconds.
                         # Let's set it to 7 seconds to be super safe. 
                         # Actually, let's try 5 seconds first as bursts might be allowed or the user message said 10 requests / min?
                         # The user message said: "quota_value: 10".
                         # So yes, 1 request every 6 seconds.
    _min_interval = 7.0 

    @classmethod
    def call_gemini(cls, model_name, prompt, retries=3):
        """
        Thread-safe(ish) wrapper for Gemini API calls with rate limiting.
        """
        # 1. Enforce Rate Limit
        elapsed = time.time() - cls._last_call_time
        if elapsed < cls._min_interval:
            wait_time = cls._min_interval - elapsed
            logger.info(f"⏳ Rate Limit: Waiting {wait_time:.1f}s...")
            time.sleep(wait_time)
        
        cls._last_call_time = time.time()

        # 2. Execute with Retry Logic
        for attempt in range(retries):
            try:
                model = gemini_client.GenerativeModel(model_name)
                response = model.generate_content(prompt)
                return response
            except Exception as e: # Catch broadly to include GoogleAPICallError
                error_str = str(e)
                if "429" in error_str or "ResourceExhausted" in error_str or "Quota exceeded" in error_str:
                    wait_time = (2 ** attempt) + random.uniform(0, 1)
                    logger.warning(f"⚠️ Quota Hit (429). Retrying in {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    cls._last_call_time = time.time() # Reset timer after wait
                else:
                    raise e # Re-raise non-quota errors
        
        raise Exception("Max retries exceeded for Gemini API call.")

def call_gemini(prompt, model_name=None):
    if not model_name:
        model_name = Config.GEMINI_MODEL_NAME
    return GeminiLimiter.call_gemini(model_name, prompt)
