"""
Free Image Provider - Pexels and Pixabay
Provides free stock images for presentations.
"""
import os
import aiohttp
import uuid
from app.core.config import config
from app.core.logger import get_logger

logger = get_logger(__name__)


async def get_image_from_pexels(query: str, output_dir: str) -> str | None:
    """
    Fetch a stock image from Pexels API.
    Free tier: 200 requests/month.
    Get API key: https://www.pexels.com/api/
    """
    api_key = getattr(config, 'PEXELS_API_KEY', None) or os.getenv('PEXELS_API_KEY')
    if not api_key:
        logger.warning("PEXELS_API_KEY not set. Skipping Pexels image.")
        return None
    
    try:
        # Clean query for search
        search_query = query.replace('"', '').replace("'", "")[:100]
        
        async with aiohttp.ClientSession() as session:
            url = f"https://api.pexels.com/v1/search?query={search_query}&per_page=1&orientation=landscape"
            headers = {"Authorization": api_key}
            
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.error(f"Pexels API error: {response.status}")
                    return None
                
                data = await response.json()
                
                if not data.get("photos"):
                    logger.warning(f"No Pexels images found for: {search_query}")
                    return None
                
                image_url = data["photos"][0]["src"]["large"]
                
                # Download the image
                async with session.get(image_url) as img_response:
                    if img_response.status == 200:
                        filename = f"{uuid.uuid4()}.jpg"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(await img_response.read())
                        
                        logger.info(f"Pexels image saved: {filepath}")
                        return filepath
                
                return None
                
    except Exception as e:
        logger.error(f"Pexels error: {e}")
        return None


async def get_image_from_pixabay(query: str, output_dir: str) -> str | None:
    """
    Fetch a stock image from Pixabay API.
    Free tier: Unlimited with attribution.
    Get API key: https://pixabay.com/api/docs/
    """
    api_key = getattr(config, 'PIXABAY_API_KEY', None) or os.getenv('PIXABAY_API_KEY')
    if not api_key:
        logger.warning("PIXABAY_API_KEY not set. Skipping Pixabay image.")
        return None
    
    try:
        search_query = query.replace('"', '').replace("'", "")[:100]
        
        async with aiohttp.ClientSession() as session:
            url = f"https://pixabay.com/api/?key={api_key}&q={search_query}&image_type=photo&orientation=horizontal&per_page=3"
            
            async with session.get(url) as response:
                if response.status != 200:
                    logger.error(f"Pixabay API error: {response.status}")
                    return None
                
                data = await response.json()
                
                if not data.get("hits"):
                    logger.warning(f"No Pixabay images found for: {search_query}")
                    return None
                
                image_url = data["hits"][0]["largeImageURL"]
                
                # Download the image
                async with session.get(image_url) as img_response:
                    if img_response.status == 200:
                        filename = f"{uuid.uuid4()}.jpg"
                        filepath = os.path.join(output_dir, filename)
                        
                        with open(filepath, 'wb') as f:
                            f.write(await img_response.read())
                        
                        logger.info(f"Pixabay image saved: {filepath}")
                        return filepath
                
                return None
                
    except Exception as e:
        logger.error(f"Pixabay error: {e}")
        return None


async def get_stock_image(query: str, output_dir: str) -> str | None:
    """
    Get a stock image from available providers.
    Tries Pexels first, then Pixabay as fallback.
    """
    # Try Pexels first
    result = await get_image_from_pexels(query, output_dir)
    if result:
        return result
    
    # Fallback to Pixabay
    result = await get_image_from_pixabay(query, output_dir)
    if result:
        return result
    
    logger.warning(f"No stock image found for: {query}")
    return None
