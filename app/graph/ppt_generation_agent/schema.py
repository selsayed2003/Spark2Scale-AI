from typing import List, Optional
from pydantic import BaseModel, Field

# --- Data Models ---

class PPTSection(BaseModel):
    title: str = Field(..., description="Title of the slide/section")
    content: List[str] = Field(..., description="Bullet points or key content for the slide")
    speaker_notes: str = Field(..., description="Narrative for the speaker")
    image_prompt: Optional[str] = Field(None, description="Detailed prompt for generating an image for this slide. If None, no image is generated.")
    image_path: Optional[str] = Field(None, description="Path to the generated image file.")
    data_visualization: Optional[str] = Field(None, description="Description of data to visualize (e.g., 'Bar chart showing 50% growth in 2024'). If None, no chart.")
    visualization_data: Optional[dict] = Field(None, description="Structured data for the chart if applicable (e.g., {'labels': ['A', 'B'], 'values': [10, 20], 'type': 'bar'}).")
    visualization_path: Optional[str] = Field(None, description="Path to the generated chart image file.")

class PPTDraft(BaseModel):
    title: str = Field(..., description="Title of the presentation")
    theme: str = Field("minimalist", description="Theme of the presentation (minimalist, professional, creative, dark_modern).")
    logo_path: Optional[str] = Field(None, description="Path to the logo image file.")
    color_palette: Optional[List[str]] = Field(None, description="List of HEX colors to use for the presentation.")
    use_default_colors: bool = Field(True, description="Whether to use default theme colors if no custom colors are provided.")
    sections: List[PPTSection] = Field(..., description="List of slides/sections")

class Critique(BaseModel):
    critique: str = Field(..., description="General feedback and specific improvement points")
    score: int = Field(..., description="Quality score from 0-100")
    recommendations: List[str] = Field(..., description="Specific list of recommended changes")
