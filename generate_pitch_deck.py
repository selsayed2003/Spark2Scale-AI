"""
Generic Pitch Deck Generator - Premium Edition
Works with any CSV input - auto-detects fields and generates high-fidelity presentations.
Uses free stock images from Pexels/Pixabay and professional layouts.
"""
import asyncio
import os
import csv
import re
import logging
import time
from typing import Optional
from app.graph.ppt_generation_agent.schema import PPTDraft, PPTSection
from app.graph.ppt_generation_agent.utils import generate_pptx_file
from app.graph.ppt_generation_agent.tools.image_provider import get_stock_image
from app.core.config import config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Paths
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INPUT_DIR = os.path.join(BASE_DIR, "app", "graph", "ppt_generation_agent", "input")
OUTPUT_DIR = os.path.join(BASE_DIR, "app", "graph", "ppt_generation_agent", "output")

# Field mapping - maps common CSV headers to standard fields
FIELD_MAPPINGS = {
    "problem": ["problem", "problem definition", "pain point", "challenge"],
    "solution": ["solution", "the solution", "product", "offering"],
    "validation": ["validation", "market validation", "proof", "evidence"],
    "market_size": ["market", "market size", "tam", "opportunity"],
    "business_model": ["business model", "revenue", "monetization", "pricing"],
    "traction": ["traction", "metrics", "growth", "users", "revenue"],
    "team": ["team", "founders", "leadership"],
    "ask": ["ask", "fundraising", "investment", "funding"],
    "company": ["company", "company name", "startup", "name"],
    "competitors": ["competitors", "competition", "landscape"],
    "advantages": ["advantages", "competitive advantages", "moat", "edges", "differentiators"]
}


def read_csv_flexible(filepath: str) -> dict:
    """Read CSV with flexible header detection."""
    data = {}
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    lines = content.strip().split('\n')
    if not lines: return data

    if ',' in lines[0]:
        reader = csv.reader(lines)
        rows = list(reader)
        
        if len(rows[0]) == 2:
            for row in rows:
                if len(row) >= 2:
                    key = row[0].strip().lower()
                    value = row[1].strip()
                    for std_field, variations in FIELD_MAPPINGS.items():
                        if any(v in key for v in variations):
                            data[std_field] = value
                            break
                    else:
                        data[key] = value
        else:
            headers = [h.strip().lower() for h in rows[0]]
            for row in rows[1:]:
                for i, value in enumerate(row):
                    if i < len(headers):
                        key = headers[i]
                        for std_field, variations in FIELD_MAPPINGS.items():
                            if any(v in key for v in variations):
                                data[std_field] = value.strip()
                                break
    else:
        data['content'] = content
    
    return data


def extract_numbers(text: str) -> dict:
    """Extract key numbers from text."""
    numbers = {}
    
    match = re.search(r'[+]?(\d+[,.]?\d*)[Kk]?\s*(?:registered\s+)?(?:users?|customers?)', text, re.I)
    if match:
        val = match.group(1).replace(',', '')
        multiplier = 1000 if 'k' in text[match.start():match.end()].lower() else 1
        numbers['users'] = int(float(val) * multiplier)
    
    match = re.search(r'\$(\d+[,.]?\d*)[Kk]?', text, re.I)
    if match:
        val = match.group(1).replace(',', '')
        multiplier = 1000 if 'k' in text[match.start():match.end()].lower() else 1
        numbers['revenue'] = int(float(val) * multiplier)
    
    match = re.search(r'TAM[:\s]*(\d+)', text, re.I)
    if match: numbers['tam'] = int(match.group(1).replace(',', ''))
    
    match = re.search(r'SAM[:\s]*(\d+)', text, re.I)
    if match: numbers['sam'] = int(match.group(1).replace(',', ''))

    return numbers


def split_into_points(text: str, max_points: int = 3) -> list:
    """Split text into 3 clean, concise bullet points."""
    # Split by semicolon, period, or comma if too long
    delimiters = [';', '.', ',']
    points = []
    
    for d in delimiters:
        if d in text:
            parts = [p.strip() for p in text.split(d) if len(p.strip()) > 5]
            if len(parts) >= 2:
                points = parts
                break
    
    if not points:
        points = [text]
    
    # Clean up and shorten
    cleaned = []
    for p in points:
        p = p.strip()
        if p.endswith('.'): p = p[:-1]
        if len(p) > 100: p = p[:97] + "..."
        if p: cleaned.append(p)
    
    return cleaned[:max_points]


async def generate_images_for_sections(sections: list[PPTSection], output_dir: str) -> None:
    """Generate professional stock images for sections."""
    for section in sections:
        if section.image_prompt and not section.image_path:
            # Clean prompt for search query
            query = section.image_prompt.split(',')[0]
            query = re.sub(r'[^\w\s]', '', query)
            
            print(f"  🖼️  Fetching premium image for: {section.title}")
            image_path = await get_stock_image(query, output_dir)
            
            if image_path:
                section.image_path = image_path
                print(f"      ✓ Image included")
            else:
                print(f"      ⚠️ Search failed, placeholder used")


def create_sections_from_data(data: dict) -> list[PPTSection]:
    """Create sections with high-quality content and prompts."""
    sections = []
    
    # 1. Problem
    problem_text = data.get('problem', 'Markets are saturated with generic options.')
    sections.append(PPTSection(
        title="The Problem",
        content=split_into_points(problem_text, 3),
        speaker_notes="State the pain point clearly.",
        image_prompt="business challenge frustration, professional photography, corporate"
    ))
    
    # 2. Solution
    solution_text = data.get('solution', 'Our AI-powered platform streamlines everything.')
    sections.append(PPTSection(
        title="Our Solution",
        content=split_into_points(solution_text, 3),
        speaker_notes="Your product is the hero.",
        image_prompt="modern technology innovation, clean bright studio lighting"
    ))
    
    # 3. Market Size - Chart
    market_text = data.get('market_size', 'TAM 2000M, SAM 200M, SOM 50M')
    nums = extract_numbers(market_text)
    tam, sam, som = nums.get('tam', 2000), nums.get('sam', 200), nums.get('som', 50)
    
    sections.append(PPTSection(
        title="Market Size",
        content=[f"TAM: {tam}M Market", f"SAM: {sam}M target", f"SOM: {som}M reachable"],
        speaker_notes=f"Massive opportunity: {tam}M TAM",
        visualization_data={
            "type": "funnel",
            "title": "Market Opportunity (M)",
            "labels": ["TAM", "SAM", "SOM"],
            "values": [tam, sam, som]
        }
    ))
    
    # 4. Product
    sections.append(PPTSection(
        title="The Product",
        content=[
            "Intuitive user interface",
            "Real-time AI processing",
            "Seamless cloud integration"
        ],
        speaker_notes="Walk through the features.",
        image_prompt="mobile app UI design, hands holding phone, minimalist"
    ))
    
    # 5. Business Model
    bm_text = data.get('business_model', 'SaaS subscription and API fees.')
    sections.append(PPTSection(
        title="Business Model",
        content=split_into_points(bm_text, 3),
        speaker_notes="Our path to revenue.",
        image_prompt="business growth financial success, corporate professional"
    ))
    
    # 6. Traction
    traction_text = data.get('traction', 'Growing at 20% month over month.')
    nums = extract_numbers(traction_text)
    sections.append(PPTSection(
        title="Traction",
        content=[
            f"{nums.get('users', 10000):,} Active Users",
            f"${nums.get('revenue', 45000):,} Revenue",
            "Market leading retention"
        ],
        speaker_notes="Real proof of growth.",
        image_prompt="startup success metrics, professional growth"
    ))
    
    # 7. Team
    team_text = data.get('team', 'Expert founders with global experience.')
    sections.append(PPTSection(
        title="The Team",
        content=split_into_points(team_text, 3),
        speaker_notes="The talent behind the tech.",
        image_prompt="professional business team, group portrait, modern office"
    ))
    
    # 8. The Ask
    ask_text = data.get('ask', '$500k for expansion.')
    sections.append(PPTSection(
        title="The Ask",
        content=split_into_points(ask_text, 3),
        speaker_notes="Invest in the future.",
        image_prompt="investment funding handshake, startup deal"
    ))
    
    return sections


async def main():
    print("=" * 60)
    print("PREMIUM PITCH DECK GENERATOR")
    print("=" * 60)
    
    # Ensure output exists
    if not os.path.exists(OUTPUT_DIR): os.makedirs(OUTPUT_DIR)
    
    # Load Data
    print("\n📂 Loading data from CSV...")
    all_data = {}
    for f in os.listdir(INPUT_DIR):
        if f.endswith('.csv'):
            all_data.update(read_csv_flexible(os.path.join(INPUT_DIR, f)))
    
    if not all_data:
        print("❌ No input data found!")
        return
    
    # 🕵️ Detect Logo
    logo_path = os.path.join(INPUT_DIR, "Logo.jpg")
    use_logo = os.path.exists(logo_path)
    if use_logo:
        print(f"🎨 Logo detected! Extracting colors for your theme...")
    
    print(f"📋 Generating for: {all_data.get('company', 'Startup')}")
    
    # Create sections
    sections = create_sections_from_data(all_data)
    
    # Get Images
    await generate_images_for_sections(sections, OUTPUT_DIR)
    
    # Create Draft
    draft = PPTDraft(
        title=all_data.get('company', 'Pitch Deck'),
        theme="creative", # Default theme if no logo
        logo_path=logo_path if use_logo else None,
        use_default_colors=not use_logo, # Use logo colors if available
        sections=sections
    )
    
    print("\n🎨 Creating premium presentation...")
    timestamp = int(time.time())
    output_path = os.path.join(OUTPUT_DIR, f"premium_pitch_deck_{timestamp}.pptx")
    
    try:
        await generate_pptx_file(draft, output_path)
        print(f"\n✅ SUCCESS! File: {output_path}")
    except Exception as e:
        print(f"\n❌ ERROR: {e}")

if __name__ == "__main__":
    asyncio.run(main())
