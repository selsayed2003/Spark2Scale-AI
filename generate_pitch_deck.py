"""
Generic Pitch Deck Generator - Premium Edition
Supports CSV or JSON input; auto-detects format and maps to presentation sections.
Uses Gemini AI to humanize and refine content for a premium feel.
"""
import asyncio
import os
import re
import logging
import time
from langchain_core.messages import SystemMessage, HumanMessage
from app.graph.ppt_generation_agent.schema import PPTDraft, PPTSection
from app.graph.ppt_generation_agent.utils import generate_pptx_file
from app.graph.ppt_generation_agent.tools.image_generator import generate_image
from app.graph.ppt_generation_agent.input_loader import load_input_directory
from app.graph.ppt_generation_agent.prompts import GENERATOR_SYSTEM_PROMPT
from app.core.llm import get_llm

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "app", "graph", "ppt_generation_agent", "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "graph", "ppt_generation_agent", "output")


async def generate_images_for_sections(sections: list[PPTSection], output_dir: str) -> None:
    """Generate professional stock images for sections using Pollinations/DALL-E."""
    loop = asyncio.get_event_loop()
    for section in sections:
        if section.image_prompt and not section.image_path:
            # Clean prompt for search query (use the first part before comma)
            query = section.image_prompt.split(',')[0]
            query = re.sub(r'[^\w\s]', '', query)
            
            print(f"  🖼️  Generating premium image for: {section.title}...")
            # Use executor for sync generate_image function
            image_path = await loop.run_in_executor(None, generate_image, query, output_dir)
            
            if image_path:
                section.image_path = image_path
                print(f"      ✓ Image included")
            else:
                print(f"      ⚠️ Generation failed, placeholder used")


async def main():
    print("=" * 60)
    print("PREMIUM PITCH DECK GENERATOR - AI REFINEMENT")
    print("=" * 60)
    
    # Ensure output exists
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    # Load Data (CSV or JSON from input folder)
    print("\n📂 Loading input data (CSV or JSON)...")
    loaded = load_input_directory(INPUT_DIR)
    research_content = loaded.research_data
    all_data = loaded.flat_data

    if not research_content:
        print("❌ No input data found. Add .csv or .json files to the input folder.")
        return
    
    if loaded.source:
        print(f"   Using {loaded.source.upper()} input.")
    
    # 🕵️ Detect Logo
    logo_path = os.path.join(INPUT_DIR, "Logo.jpg")
    use_logo = os.path.exists(logo_path)
    if use_logo:
        print(f"🎨 Logo detected! AI will integrate your brand colors...")
    
    print(f"📋 Processing Content for: {all_data.get('company', 'Your Startup')}")
    print("🧠 Humanizing content with Gemini AI (Catchy & Premium Phrasing)...")

    # 🤖 Invoke LLM for catchy content
    llm = get_llm()
    structured_llm = llm.with_structured_output(PPTDraft)
    
    try:
        # Generate the draft using the system prompt for catchy/human feel
        draft: PPTDraft = await structured_llm.ainvoke([
            SystemMessage(content=GENERATOR_SYSTEM_PROMPT),
            HumanMessage(content=f"""
                Create a premium, catchy pitch presentation from the research below.
                
                Rules: 
                - Do NOT copy-paste sentences. 
                - Rewrite every slide to be punchy, human, and memorable.
                - Use "we" and "you" to humanize the message.
                - Bold impact words using <b>...</b>.
                
                Research Data:
                {research_content}
            """),
        ])

        # Apply logo and metadata
        draft.logo_path = logo_path if use_logo else None
        draft.use_default_colors = not use_logo
        
        # 🖼️ Get Images for the AI-generated sections
        await generate_images_for_sections(draft.sections, OUTPUT_DIR)
        
        print("\n🎨 Creating premium presentation...")
        timestamp = int(time.time())
        output_name = f"premium_pitch_deck_{timestamp}.pptx"
        output_path = os.path.join(OUTPUT_DIR, output_name)
        
        await generate_pptx_file(draft, output_path)
        print(f"\n✅ SUCCESS! File: {output_path}")
        print(f"💡 Tip: Look for {output_name} in the output folder.")

    except Exception as e:
        print(f"\n❌ ERROR during AI generation: {e}")
        logger.error(f"AI Generation failed: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())
