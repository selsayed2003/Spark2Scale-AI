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

    # 1. Resolve Theme early (to use for charts)
    from .themes import get_theme_config, Theme, create_dynamic_theme, extract_colors_from_image
    theme_config = None
    if draft.color_palette and not draft.use_default_colors:
        theme_config = create_dynamic_theme(draft.color_palette, theme_name="Custom Palette")
    elif draft.logo_path and not draft.use_default_colors:
        extracted_colors = extract_colors_from_image(draft.logo_path)
        if extracted_colors:
            theme_config = create_dynamic_theme(extracted_colors, theme_name="Logo Derived")
    if not theme_config:
        theme_config = get_theme_config(Theme(draft.theme))
    
    c = theme_config.colors
    # Matplotlib needs '#' prefix, but ThemeConfig uses bare hex for python-pptx
    chart_palette = [f"#{c.primary}", f"#{c.secondary}", f"#{c.accent}", f"#{c.text_secondary}", f"#{c.text_primary}"]
    font_name = theme_config.fonts.header

    # 2. Generate Assets (Images & Charts)
    logger.info("Generating assets for presentation...")
    for i, section in enumerate(draft.sections):
        # Image Generation
        if section.image_prompt:
            if not section.image_path or not os.path.exists(section.image_path):
                logger.info(f"Generating image for slide {i+1}: {section.image_prompt}")
                loop = asyncio.get_event_loop()
                image_path = await loop.run_in_executor(None, generate_image, section.image_prompt, temp_dir)
                section.image_path = image_path
        
        # Chart Generation: Pass theme colors and font!
        if section.visualization_data:
            if not section.visualization_path or not os.path.exists(section.visualization_path):
                logger.info(f"Generating theme-coherent chart for slide {i+1}")
                loop = asyncio.get_event_loop()
                chart_path = await loop.run_in_executor(None, generate_chart, section.visualization_data, temp_dir, chart_palette, font_name)
                section.visualization_path = chart_path

    # 2. Map simplified Draft -> Complex PptxModel
    pptx_model = map_draft_to_pptx_model(draft)
    
    # 3. Initialize Creator
    creator = PptxPresentationCreator(pptx_model, temp_dir)
    
    # 4. Create and Save
    await creator.create_ppt()
    creator.save(output_path)
    
    return output_path
