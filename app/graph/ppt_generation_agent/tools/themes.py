import os
from enum import Enum
from pydantic import BaseModel
from typing import Optional, List
from PIL import Image
import logging

logger = logging.getLogger(__name__)

def extract_colors_from_image(image_path: str, num_colors: int = 5) -> List[str]:
    """
    Extracts dominant colors from an image and returns them as a list of HEX strings.
    """
    try:
        if not os.path.exists(image_path):
            logger.warning(f"Image path does not exist: {image_path}")
            return []

        img = Image.open(image_path)
        img = img.convert("P", palette=Image.ADAPTIVE, colors=num_colors)
        img = img.convert("RGB")
        
        # Get dominant colors
        colors = img.getcolors(num_colors * num_colors)
        if not colors:
            return []
            
        # Sort by count (most frequent first)
        colors.sort(key=lambda x: x[0], reverse=True)
        
        hex_colors = []
        for count, rgb in colors[:num_colors]:
            hex_colors.append('%02x%02x%02x'.upper() % rgb)
            
        return hex_colors
    except Exception as e:
        logger.error(f"Error extracting colors from image {image_path}: {e}")
        return []

class ThemeColor(BaseModel):
    primary: str
    secondary: str
    accent: str
    background: str
    text_primary: str
    text_secondary: str

class ThemeFont(BaseModel):
    header: str
    body: str

class ThemeConfig(BaseModel):
    name: str
    description: str
    colors: ThemeColor
    fonts: ThemeFont

class Theme(str, Enum):
    MINIMALIST = "minimalist"
    PROFESSIONAL = "professional"
    CREATIVE = "creative"
    DARK_MODERN = "dark_modern"

THEMES = {
    Theme.MINIMALIST: ThemeConfig(
        name="Minimalist",
        description="Clean, white background, black text, simple fonts.",
        colors=ThemeColor(
            primary="000000",
            secondary="666666",
            accent="333333",
            background="FFFFFF",
            text_primary="000000",
            text_secondary="666666"
        ),
        fonts=ThemeFont(header="Arial", body="Arial")
    ),
    Theme.PROFESSIONAL: ThemeConfig(
        name="Professional",
        description="Corporate blue tones, standard business look.",
        colors=ThemeColor(
            primary="003366", # Navy Blue
            secondary="0055A4", # Lighter Blue
            accent="FF9900", # Orange accent
            background="FFFFFF",
            text_primary="000000",
            text_secondary="333333"
        ),
        fonts=ThemeFont(header="Calibri", body="Calibri")
    ),
    Theme.CREATIVE: ThemeConfig(
        name="Creative",
        description="Vibrant colors, playful fonts.",
        colors=ThemeColor(
            primary="FF3366", # Pink/Red
            secondary="663399", # Purple
            accent="00CC99", # Teal
            background="FAFAFA",
            text_primary="333333",
            text_secondary="555555"
        ),
        fonts=ThemeFont(header="Verdana", body="Verdana")
    ),
    Theme.DARK_MODERN: ThemeConfig(
        name="Dark Modern",
        description="Dark background, light text, sleek look.",
        colors=ThemeColor(
            primary="FFFFFF",
            secondary="CCCCCC",
            accent="00ADB5", # Cyan
            background="222831", # Dark Grey
            text_primary="EEEEEE",
            text_secondary="AAAAAA"
        ),
        fonts=ThemeFont(header="Segoe UI", body="Segoe UI")
    )
}

def get_theme_config(theme: Theme) -> ThemeConfig:
    return THEMES.get(theme, THEMES[Theme.MINIMALIST])

def create_dynamic_theme(colors: List[str], theme_name: str = "Dynamic") -> ThemeConfig:
    """
    Creates a ThemeConfig from a list of HEX colors.
    """
    if not colors or len(colors) < 1:
        # Fallback to minimalist
        return THEMES[Theme.MINIMALIST]
        
    # Assign colors with fallbacks and strip '#' if present
    def normalize(c: str) -> str:
        return c.lstrip('#').upper()

    primary = normalize(colors[0])
    secondary = normalize(colors[1]) if len(colors) > 1 else primary
    accent = normalize(colors[2]) if len(colors) > 2 else secondary
    background = "FFFFFF" 
    text_primary = "000000"
    text_secondary = "333333"
    
    return ThemeConfig(
        name=theme_name,
        description=f"Dynamically generated theme from colors: {', '.join(colors)}",
        colors=ThemeColor(
            primary=primary,
            secondary=secondary,
            accent=accent,
            background=background,
            text_primary=text_primary,
            text_secondary=text_secondary
        ),
        fonts=ThemeFont(header="Arial", body="Arial")
    )
