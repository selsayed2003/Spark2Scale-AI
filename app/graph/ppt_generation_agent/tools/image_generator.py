import os
import requests
import uuid
from app.core.config import config
from app.core.logger import get_logger

logger = get_logger(__name__)

def generate_image(prompt: str, output_dir: str) -> str:
    """
    Generates an image using Hugging Face API and saves it to output_dir.
    Returns the path to the generated image.
    """
    if not config.HUGGINGFACE_API_TOKEN:
        logger.warning("HUGGINGFACE_API_TOKEN is not set. Skipping image generation.")
        return None

    model_name = config.HUGGINGFACE_MODEL.strip("'\"")
    api_url = f"https://router.huggingface.co/hf-inference/models/{model_name}"
    headers = {"Authorization": f"Bearer {config.HUGGINGFACE_API_TOKEN}"}
    
    payload = {
        "inputs": prompt,
    }

    try:
        logger.info(f"Generating image for prompt: {prompt}")
        response = requests.post(api_url, headers=headers, json=payload, timeout=30)
        
        if response.status_code != 200:
            error_data = response.json() if response.status_code != 500 else {"error": "Server error"}
            logger.error(f"Image generation failed ({response.status_code}): {error_data}")
            return None

        image_bytes = response.content
        
        filename = f"{uuid.uuid4()}.png"
        filepath = os.path.join(output_dir, filename)
        
        with open(filepath, "wb") as f:
            f.write(image_bytes)
            
        logger.info(f"Image saved to {filepath}")
        return filepath

    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return None
