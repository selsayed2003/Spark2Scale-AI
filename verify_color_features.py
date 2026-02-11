import os
import sys
from PIL import Image, ImageDraw

# Add app directory to sys.path
sys.path.append(os.getcwd())

from app.graph.ppt_generation_agent.themes import extract_colors_from_image, create_dynamic_theme
from app.graph.ppt_generation_agent.schema import PPTDraft

def create_test_image(path: str):
    """Creates a simple test image with specific colors."""
    img = Image.new('RGB', (100, 100), color=(255, 0, 0)) # Red background
    draw = ImageDraw.Draw(img)
    draw.rectangle([25, 25, 75, 75], fill=(0, 255, 0))    # Green square
    draw.ellipse([40, 40, 60, 60], fill=(0, 0, 255))      # Blue circle
    img.save(path)
    print(f"Created test image at: {path}")

def test_color_extraction():
    test_image = "test_logo.png"
    create_test_image(test_image)
    
    print("\n--- Testing Color Extraction ---")
    colors = extract_colors_from_image(test_image)
    print(f"Extracted colors: {colors}")
    
    assert len(colors) > 0, "No colors extracted"
    print("✓ Success: Colors extracted")
    
    print("\n--- Testing Dynamic Theme Creation ---")
    theme = create_dynamic_theme(colors)
    print(f"Theme Name: {theme.name}")
    print(f"Primary Color: {theme.colors.primary}")
    print(f"Secondary Color: {theme.colors.secondary}")
    print(f"Accent Color: {theme.colors.accent}")
    
    assert theme.colors.primary == colors[0], "Primary color mismatch"
    print("✓ Success: Dynamic theme created correctly")
    
    # Cleanup
    if os.path.exists(test_image):
        os.remove(test_image)

if __name__ == "__main__":
    try:
        test_color_extraction()
        print("\nALL TESTS PASSED!")
    except Exception as e:
        print(f"\nTEST FAILED: {e}")
        import traceback
        traceback.print_exc()
