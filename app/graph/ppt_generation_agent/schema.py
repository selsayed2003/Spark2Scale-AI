# from typing import List
# from pydantic import BaseModel, Field
# from pptx import Presentation

# # --- Data Models ---

# class PPTSection(BaseModel):
#     title: str = Field(..., description="Title of the slide/section")
#     content: List[str] = Field(..., description="Bullet points or key content for the slide")
#     speaker_notes: str = Field(..., description="Narrative for the speaker")

# class PPTDraft(BaseModel):
#     title: str = Field(..., description="Title of the presentation")
#     sections: List[PPTSection] = Field(..., description="List of slides/sections")

# class Critique(BaseModel):
#     critique: str = Field(..., description="General feedback and specific improvement points")
#     score: int = Field(..., description="Quality score from 0-100")
#     recommendations: List[str] = Field(..., description="Specific list of recommended changes")

# # --- Helper Tools ---

# def create_slide(title, content):
#     prs = Presentation()
#     slide_layout = prs.slide_layouts[0]
#     slide = prs.slides.add_slide(slide_layout)
#     title_placeholder = slide.shapes.title
#     subtitle_placeholder = slide.placeholders[1]
    
#     title_placeholder.text = title
#     subtitle_placeholder.text = content
    
#     prs.save('test.pptx')
#     return "Slide created"
