from typing import List
import uuid

from .schema import PPTDraft, PPTSection
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_AUTO_SHAPE_TYPE
from .presenton_core.models.pptx_models import (
    PptxPresentationModel,
    PptxSlideModel,
    PptxTextBoxModel,
    PptxAutoShapeBoxModel,
    PptxPositionModel,
    PptxParagraphModel,
    PptxFontModel,
    PptxSpacingModel,
    PptxTextRunModel,
    PptxFillModel,
    PptxStrokeModel,
    PptxShadowModel,
    PptxPictureBoxModel,
    PptxPictureModel,
    PptxObjectFitEnum,
    PptxObjectFitModel,
)
from .themes import get_theme_config, Theme, create_dynamic_theme, extract_colors_from_image

def map_draft_to_pptx_model(draft: PPTDraft) -> PptxPresentationModel:
    slides: List[PptxSlideModel] = []
    
    # --- Theme and Color Selection Logic ---
    theme_config = None
    
    # 1. Check for manual color palette
    if draft.color_palette and not draft.use_default_colors:
        theme_config = create_dynamic_theme(draft.color_palette, theme_name="Custom Palette")
    
    # 2. Check for logo-based colors
    elif draft.logo_path and not draft.use_default_colors:
        extracted_colors = extract_colors_from_image(draft.logo_path)
        if extracted_colors:
            theme_config = create_dynamic_theme(extracted_colors, theme_name="Logo Derived")
    
    # 3. Fallback to default theme
    if not theme_config:
        theme_config = get_theme_config(Theme(draft.theme))
        
    colors = theme_config.colors
    fonts = theme_config.fonts

    # Standard Margins and Sizing (Presenton uses 1280x720 internal units)
    WIDTH = 1280
    HEIGHT = 720
    
    # --- Title Slide (premium: larger, bolder) ---
    title_slide = PptxSlideModel(
        background=PptxFillModel(color=colors.background),
        shapes=[
            PptxTextBoxModel(
                position=PptxPositionModel(left=80, top=230, width=1120, height=180),
                paragraphs=[
                    PptxParagraphModel(
                        text=draft.title,
                        font=PptxFontModel(
                            size=64,
                            font_weight=700,
                            name=fonts.header,
                            color=colors.primary
                        ),
                        alignment=PP_ALIGN.CENTER
                    )
                ],
                text_wrap=True
            ),
            PptxTextBoxModel(
                position=PptxPositionModel(left=80, top=440, width=1120, height=60),
                paragraphs=[
                    PptxParagraphModel(
                        text="POWERED BY SPARK2SCALE AI",
                        font=PptxFontModel(
                            size=20,
                            font_weight=600,
                            name=fonts.body,
                            color=colors.accent
                        ),
                        alignment=PP_ALIGN.CENTER
                    )
                ]
            )
        ]
    )

    # Add Logo to Title Slide if provided
    if draft.logo_path:
        title_slide.shapes.append(
            PptxPictureBoxModel(
                position=PptxPositionModel(left=50, top=50, width=120, height=80),
                picture=PptxPictureModel(path=draft.logo_path, is_network=False),
                object_fit=PptxObjectFitModel(fit=PptxObjectFitEnum.CONTAIN)
            )
        )
    
    slides.append(title_slide)
    
    # --- Content Slides ---
    for section in draft.sections:
        shapes = []
        
        # 1. Slide Title (premium: bigger, bolder)
        shapes.append(
            PptxTextBoxModel(
                position=PptxPositionModel(left=60, top=35, width=1160, height=90),
                paragraphs=[
                    PptxParagraphModel(
                        text=section.title.upper(),
                        font=PptxFontModel(
                            size=40,
                            font_weight=800,
                            name=fonts.header,
                            color=colors.primary
                        )
                    )
                ]
            )
        )
        
        # 2. Determine Layout
        has_visual = bool(section.image_path or section.visualization_path)
        
        if has_visual:
            # Split Layout: Text (Left) + Image/Chart (Right)
            asset_path = section.visualization_path if section.visualization_path else section.image_path
            
            # Text Cards (premium: bigger body; bold runs use accent color)
            card_width = 540
            body_font = PptxFontModel(size=22, name=fonts.body, color=colors.text_primary)
            highlight_font = PptxFontModel(size=22, name=fonts.body, color=colors.accent, font_weight=700)
            for i, bullet in enumerate(section.content[:3]):
                card_y = 150 + (i * 158)
                shapes.append(
                    PptxTextBoxModel(
                        position=PptxPositionModel(left=60, top=card_y, width=card_width, height=145),
                        paragraphs=[
                            PptxParagraphModel(
                                text=bullet,
                                font=body_font,
                                highlight_font=highlight_font
                            )
                        ]
                    )
                )

            # Large Image/Chart Card (Right side)
            shapes.append(
                PptxPictureBoxModel(
                    position=PptxPositionModel(left=660, top=150, width=560, height=460),
                    picture=PptxPictureModel(
                        path=asset_path,
                        is_network=False
                    ),
                    border_radius=[20, 20, 20, 20],
                    object_fit=PptxObjectFitModel(fit=PptxObjectFitEnum.COVER)
                )
            )
        else:
            # Full Width 3-Column (premium: bigger body; bold = accent color)
            col_width = 360
            body_font = PptxFontModel(size=24, name=fonts.body, color=colors.text_primary)
            highlight_font = PptxFontModel(size=24, name=fonts.body, color=colors.accent, font_weight=700)
            for i, bullet in enumerate(section.content[:3]):
                col_x = 60 + (i * 400)
                shapes.append(
                    PptxTextBoxModel(
                        position=PptxPositionModel(left=col_x, top=175, width=col_width, height=410),
                        paragraphs=[
                            PptxParagraphModel(
                                text=bullet,
                                font=body_font,
                                highlight_font=highlight_font,
                                alignment=PP_ALIGN.CENTER
                            )
                        ]
                    )
                )
        
        # Add Logo Watermark to Slide (Top Right)
        if draft.logo_path:
            shapes.append(
                PptxPictureBoxModel(
                    position=PptxPositionModel(left=1100, top=30, width=120, height=80),
                    picture=PptxPictureModel(path=draft.logo_path, is_network=False),
                    object_fit=PptxObjectFitModel(fit=PptxObjectFitEnum.CONTAIN)
                )
            )
                
        slide = PptxSlideModel(
            background=PptxFillModel(color=colors.background),
            shapes=shapes,
            note=section.speaker_notes or ""
        )
        slides.append(slide)
        
    return PptxPresentationModel(
        name=draft.title,
        slides=slides
    )
