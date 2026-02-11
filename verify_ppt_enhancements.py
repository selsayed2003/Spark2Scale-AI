import asyncio
import os
import logging
from app.graph.ppt_generation_agent.schema import PPTDraft, PPTSection
from app.graph.ppt_generation_agent.utils import generate_pptx_file
from app.core.config import config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    print("Starting PPT Enhancement Verification...")
    
    # Check for Hugging Face Token
    if not config.HUGGINGFACE_API_TOKEN:
        print("WARNING: HUGGINGFACE_API_TOKEN is not set. Image generation will be skipped.")
    else:
        print("HUGGINGFACE_API_TOKEN is set.")

    # Create a mock draft
    draft = PPTDraft(
        title="Future of AI in Baking",
        theme="creative",
        sections=[
            PPTSection(
                title="The Rise of Smart Ovens",
                content=[
                    "AI-controlled temperature regulation.",
                    "Automatic bread sensing.",
                    "Energy efficiency improvements."
                ],
                speaker_notes="Discuss how smart ovens are changing the game.",
                image_prompt="A futuristic smart oven with glowing holographic interface baking bread, cyberpunk style"
            ),
            PPTSection(
                title="Market Growth",
                content=[
                    "50% year-over-year growth.",
                    "Adoption in both commercial and home kitchens.",
                    "Projected market size of $5B by 2030."
                ],
                speaker_notes="Highlight the massive growth potential.",
                data_visualization="Bar chart showing market growth from 2020 to 2030",
                visualization_data={
                    "type": "bar",
                    "title": "Smart Oven Market Size (Billions USD)",
                    "labels": ["2020", "2022", "2024", "2026", "2028", "2030"],
                    "values": [0.5, 1.2, 2.0, 3.1, 4.2, 5.0],
                    "x_label": "Year",
                    "y_label": "Market Size ($B)"
                }
            ),
            PPTSection(
                title="Conclusion",
                content=[
                    "AI is essential for modern baking.",
                    "Invest now to stay ahead.",
                    "The future is delicious."
                ],
                speaker_notes="Wrap up with a call to action."
            )
        ]
    )
    
    output_dir = os.path.join(os.getcwd(), "verification_output")
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_path = os.path.join(output_dir, "enhanced_presentation.pptx")
    
    print(f"Generating PPT at {output_path}...")
    try:
        await generate_pptx_file(draft, output_path)
        
        if os.path.exists(output_path):
            print(f"SUCCESS: PPTX file created at {output_path}")
            print("Please open the file to verify the 'creative' theme, image on slide 1, and chart on slide 2.")
        else:
            print("FAILURE: PPTX file was not found.")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
