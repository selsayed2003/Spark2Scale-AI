import os
from .schema import PPTDraft
from .ppt_mapper import map_draft_to_pptx_model
from .presenton_core.services.pptx_presentation_creator import PptxPresentationCreator

async def generate_pptx_file(draft: PPTDraft, output_path: str) -> str:
    """
    Generates a PPTX file from a PPTDraft object using the Presenton engine.
    """
    # 1. Map simplified Draft -> Complex PptxModel
    pptx_model = map_draft_to_pptx_model(draft)
    
    # 2. Initialize Creator
    temp_dir = os.path.dirname(output_path)
    if not os.path.exists(temp_dir):
        os.makedirs(temp_dir)
        
    creator = PptxPresentationCreator(pptx_model, temp_dir)
    
    # 3. Create and Save
    await creator.create_ppt()
    creator.save(output_path)
    
    return output_path
