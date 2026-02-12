import os
import requests
import uuid
import urllib.parse
from typing import Optional

from app.core.config import config
from app.core.logger import get_logger

logger = get_logger(__name__)


def _generate_image_pollinations(prompt: str, output_dir: str) -> Optional[str]:
    """Generate image via Pollinations AI. Model is configurable (e.g. gptimage-large for better icon quality)."""
    icon_suffix = ", simple flat icon, minimal, single concept, clean vector style, white or solid background, no detailed scene"
    full_prompt = (prompt.strip().rstrip(".,") + " " + icon_suffix).strip()
    model = getattr(config, "IMAGE_MODEL", "gptimage-large") or "gptimage-large"
    logger.info(f"Generating image via Pollinations (model={model}) for prompt: {full_prompt}")
    encoded_prompt = urllib.parse.quote(full_prompt)
    seed = uuid.uuid4().int % 1000000
    url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?model={urllib.parse.quote(model)}&width=1024&height=1024&seed={seed}&nologo=true"
    headers = {}
    if config.POLLINATIONS_API_KEY:
        headers["Authorization"] = f"Bearer {config.POLLINATIONS_API_KEY}"
    response = requests.get(url, headers=headers, timeout=90)
    if response.status_code != 200:
        logger.error(f"Pollinations AI failed ({response.status_code}): {response.text}")
        return None
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "wb") as f:
        f.write(response.content)
    logger.info(f"Image saved to {filepath}")
    return filepath


def _generate_image_openai(prompt: str, output_dir: str) -> Optional[str]:
    """Generate image via OpenAI DALL-E 3 (higher quality, requires OPENAI_API_KEY)."""
    try:
        from openai import OpenAI
    except ImportError:
        logger.warning("openai package not installed. Install with: pip install openai")
        return None
    if not config.OPENAI_API_KEY:
        logger.warning("OPENAI_API_KEY not set; falling back to Pollinations.")
        return None
    icon_suffix = ", simple flat icon, minimal, single concept, clean vector style, white or solid background"
    full_prompt = (prompt.strip().rstrip(".,") + " " + icon_suffix).strip()
    logger.info(f"Generating image via OpenAI DALL-E 3 for prompt: {full_prompt}")
    client = OpenAI(api_key=config.OPENAI_API_KEY)
    resp = client.images.generate(
        model="dall-e-3",
        prompt=full_prompt,
        size="1024x1024",
        quality="standard",
        style="natural",
        n=1,
    )
    image_url = resp.data[0].url
    if not image_url:
        return None
    img_response = requests.get(image_url, timeout=60)
    img_response.raise_for_status()
    filename = f"{uuid.uuid4()}.png"
    filepath = os.path.join(output_dir, filename)
    with open(filepath, "wb") as f:
        f.write(img_response.content)
    logger.info(f"Image saved to {filepath}")
    return filepath


def generate_image(prompt: str, output_dir: str) -> Optional[str]:
    """
    Generates an image for the slide. Uses OpenAI DALL-E 3 if IMAGE_PROVIDER=openai and
    OPENAI_API_KEY is set; otherwise uses Pollinations (model from IMAGE_MODEL, e.g. gptimage-large).
    """
    try:
        provider = getattr(config, "IMAGE_PROVIDER", "pollinations") or "pollinations"
        if provider.lower() == "openai" and getattr(config, "OPENAI_API_KEY", None):
            out = _generate_image_openai(prompt, output_dir)
            if out:
                return out
            logger.info("OpenAI image failed or skipped; falling back to Pollinations.")
        return _generate_image_pollinations(prompt, output_dir)
    except Exception as e:
        logger.error(f"Error generating image: {e}")
        return None
