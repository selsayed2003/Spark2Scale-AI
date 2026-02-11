import os
import asyncio
from .schema import PPTDraft
from .ppt_mapper import map_draft_to_pptx_model
from .presenton_core.services.pptx_presentation_creator import PptxPresentationCreator
from .tools.image_generator import generate_image
from .tools.chart_generator import generate_chart
from app.core.logger import get_logger

from typing import List
from PIL import Image

logger = get_logger(__name__)


async def generate_pptx_file(draft: PPTDraft, output_path: str) -> str:
    """
    Generates a PPTX file from a PPTDraft object using the Presenton engine.
    """
    temp_dir = os.path.dirname(output_path)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)

    # 1. Generate Assets (Images & Charts)
    logger.info("Generating assets for presentation...")
    for i, section in enumerate(draft.sections):
        # Image Generation: Only skip if path exists
        if section.image_prompt:
            if not section.image_path or not os.path.exists(section.image_path):
                logger.info(f"Generating image for slide {i+1}: {section.image_prompt}")
                loop = asyncio.get_event_loop()
                image_path = await loop.run_in_executor(None, generate_image, section.image_prompt, temp_dir)
                section.image_path = image_path # Will be None if it fails, which is safe
        
        # Chart Generation: Only skip if path exists
        if section.visualization_data:
            if not section.visualization_path or not os.path.exists(section.visualization_path):
                logger.info(f"Generating chart for slide {i+1}")
                loop = asyncio.get_event_loop()
                chart_path = await loop.run_in_executor(None, generate_chart, section.visualization_data, temp_dir)
                section.visualization_path = chart_path # Will be None if it fails

    # 2. Map simplified Draft -> Complex PptxModel
    pptx_model = map_draft_to_pptx_model(draft)
    
    # 3. Initialize Creator
    creator = PptxPresentationCreator(pptx_model, temp_dir)
    
    # 4. Create and Save
    await creator.create_ppt()
    creator.save(output_path)
    
    return output_path
