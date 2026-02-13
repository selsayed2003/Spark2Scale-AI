import os
import glob
import pandas as pd
import platform
import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF

from app.core.config import settings, gemini_client
from app.graph.market_research_agent import prompts
from app.graph.market_research_agent.logger_config import get_logger
import json
import asyncio
import re

logger = get_logger("PDFUtils")

def generate_report(file_path: str, query: str, trend_file=None, finance_file=None):
    logger.info(f"\n📝 [Tool 5] Synthesizing Data & Calculating Opportunity Score...")
    
    pain_score = 50
    val_data = ""
    if file_path and os.path.exists(file_path):
        with open(file_path, 'r') as f: 
            val_data = f.read()
            try: 
                d = json.loads(val_data)
                pain_score = d.get('pain_score', 50)
            except: pass

    growth_pct = 0
    trend_summary = "No trend data."
    if trend_file and os.path.exists(trend_file):
        try:
            stats = pd.read_csv("data_output/market_stats.csv")
            growth_row = stats[stats['metric'] == 'growth_pct']
            if not growth_row.empty:
                growth_pct = float(growth_row.iloc[0]['value'])
                trend_summary = f"12-Month Growth: {growth_pct:.1f}%"
        except: pass

    finance_summary = "No financial projections available."
    if finance_file and os.path.exists(finance_file):
        try:
            df_fin = pd.read_csv(finance_file)
            finance_summary = df_fin.to_string(index=False)
        except: pass

    growth_score = max(0, min(100, growth_pct + 50))
    opp_score = (pain_score * 0.6) + (growth_score * 0.4)
    grade = "C"
    if opp_score > 80: grade = "A (Gold Mine)"
    elif opp_score > 60: grade = "B (Solid)"
    
    if not val_data: val_data = "Validation data was not generated."

    prompt = prompts.investment_memo_prompt(query, pain_score, growth_pct, grade, opp_score, finance_summary, val_data)
    try:
        # Gemini Call
        res = gemini_client.GenerativeModel(settings.GEMINI_MODEL_NAME).generate_content(prompt)
        content = res.text
        with open("data_output/FINAL_MARKET_REPORT.md", "w", encoding="utf-8") as f: f.write(content)
        logger.info(f"✅ Final Report Saved.")
    except Exception as e: logger.error(f"⚠️ Report Error: {e}")

class PDFReport(FPDF):
    # Brand Colors
    COLOR_MOSS = (87, 98, 56)      # #576238
    COLOR_MUSTARD = (255, 217, 93) # #FFD95D
    COLOR_EGGSHELL = (240, 234, 220) # #F0EADC
    COLOR_DARK_TEXT = (40, 40, 40)

    def __init__(self, orientation='P', unit='mm', format='A4'):
        super().__init__(orientation, unit, format)
        
        # Load Calibri Fonts (Windows) - "Neater & Smoother"
        self.font_family = 'Arial' # Default fallback
        try:
            # Check for Calibri files
            font_dir = r"C:\Windows\Fonts"
            if os.path.exists(os.path.join(font_dir, "calibri.ttf")):
                self.add_font("Calibri", style="", fname=os.path.join(font_dir, "calibri.ttf"), uni=True)
                self.add_font("Calibri", style="B", fname=os.path.join(font_dir, "calibrib.ttf"), uni=True)
                self.add_font("Calibri", style="I", fname=os.path.join(font_dir, "calibrii.ttf"), uni=True)
                self.add_font("Calibri", style="BI", fname=os.path.join(font_dir, "calibriz.ttf"), uni=True)
                self.font_family = 'Calibri'
            else:
                 # Fallback
                self.add_font("ArialUnicode", style="", fname=os.path.join(font_dir, "arial.ttf"), uni=True)
                self.add_font("ArialUnicode", style="B", fname=os.path.join(font_dir, "arialbd.ttf"), uni=True)
                self.font_family = 'ArialUnicode'
        except Exception as e:
            print(f"Font Warning: {e}")

    def header(self):
        # 1. Background Color (Eggshell) - Covers entire page
        # Save current state
        self.set_fill_color(*self.COLOR_EGGSHELL)
        self.rect(0, 0, 210, 297, 'F')
        
        # 2. Header Content
        self.set_font_for_content('B', 14) # Increased to 14
        # Moss Color for Header Text
        self.set_text_color(*self.COLOR_MOSS)
        self.cell(0, 10, 'Spark2Scale AI - Market Research Report', 0, 1, 'R')
        
        # Decorative Line in Mustard
        self.set_draw_color(*self.COLOR_MUSTARD)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        
        # --- NEW: PAGE BORDER (CONTAINED LOOK) ---
        self.set_draw_color(*self.COLOR_MOSS)
        self.set_line_width(0.5)
        self.rect(5, 5, 200, 287) # Margins of 5mm
        
        self.ln(5)

    def write_markdown(self, text, line_height=6):
        """
        Parses `**bold**` markdown and writes text with mixed styles.
        """
        if not text: return
        
        # Split by newlines to handle paragraphs
        lines = text.split('\n')
        for line in lines:
            if not line.strip():
                self.ln(line_height) # Empty line -> vertical space
                continue
            
            clean_line = line.strip()
            is_header = False
            header_level = 0
            
            # Detect Header
            if clean_line.startswith('### '):
                header_level = 3
                line = clean_line[4:]
                is_header = True
            elif clean_line.startswith('## '):
                header_level = 2
                line = clean_line[3:]
                is_header = True
            elif clean_line.startswith('# '):
                header_level = 1
                line = clean_line[2:]
                is_header = True
            
            # Set Font for Line
            if is_header:
                self.set_font_for_content('B', 14 - (header_level * 1)) # Sizes: 13, 12, 11...
                self.set_text_color(*self.COLOR_MOSS)
            else:
                self.set_font_for_content('', 12)
                self.set_text_color(*self.COLOR_DARK_TEXT)
            
            parts = line.split('**')
            for i, part in enumerate(parts):
                processed_text = fix_arabic(part)
                
                if i % 2 == 1: # BOLD
                    if not is_header:
                        self.set_font_for_content('B', 12)
                    self.write(line_height, processed_text)
                    if not is_header:
                        self.set_font_for_content('', 12) 
                else: # Regular
                    self.write(line_height, processed_text)
            
            self.ln(line_height)

    def draw_score_bar(self, label, score, max_score=100):
        """Draws a visual progress bar for a score."""
        self.ln(5)
        self.set_font_for_content('B', 14) # Increased to 14
        self.set_text_color(*self.COLOR_MOSS)
        self.cell(0, 10, f"{label}: {score}/{max_score}", 0, 1, 'L')
        
        # Bar dimensions
        bar_width = 160
        bar_height = 8
        start_x = 15
        
        # Background Bar (White or lighter Eggshell? White to stand out on Eggshell)
        self.set_fill_color(255, 255, 255)
        self.rect(start_x, self.get_y(), bar_width, bar_height, 'F')
        
        # Foreground Bar (Mustard or Moss based on score? Let's use Mustard for "energy" or Moss for "solid")
        # Let's use Moss for high scores, Mustard for medium? 
        # Plan said: "Moss or Mustard". Let's use Mustard for the bar to contrast with Moss text.
        self.set_fill_color(*self.COLOR_MUSTARD)
        
        fill_width = (score / max_score) * bar_width
        self.rect(start_x, self.get_y(), fill_width, bar_height, 'F')
        
        self.ln(bar_height + 5)

    def footer(self):
        self.set_y(-15)
        # Decorative Line in Mustard above footer
        self.set_draw_color(*self.COLOR_MUSTARD)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        
        self.set_font("Arial", 'I', 8)
        # Moss Color for Footer Text (Lighter or same)
        self.set_text_color(*self.COLOR_MOSS)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font_for_content('B', 18) # Increased to 18
        # Moss Color for Title
        self.set_text_color(*self.COLOR_MOSS)
        
        # Add a left accent bar in Mustard
        self.set_fill_color(*self.COLOR_MUSTARD)
        self.rect(8, self.get_y() + 2, 1, 6, 'F') # Small vertical bar
        
        self.set_x(12) # Indent slightly
        self.cell(0, 10, label.upper(), 0, 1, 'L')
        self.ln(2)
        
        # Underline in Moss (Thin) instead of Mustard to avoid too much yellow
        self.set_draw_color(*self.COLOR_MOSS)
        self.set_line_width(0.5)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def chapter_body(self, text):
        self.write_markdown(text)
        self.ln()

    def add_image_centered(self, image_path, height=80):
        if os.path.exists(image_path):
            try:
                self.image(image_path, x=15, w=180)
                self.ln(5)
            except: pass
        else:
            self.set_font("Arial", 'I', 10)
            self.set_text_color(255, 0, 0)
            self.cell(0, 10, f'[Image Missing: {os.path.basename(image_path)}]', 0, 1)

    def set_font_for_content(self, style, size):
        try:
            self.set_font(self.font_family, style, size)
        except:
            self.set_font('Arial', style, size)

def remove_emojis(text):
    if not isinstance(text, str): return text
    # Remove emojis using regex (range of emojis)
    # Allow common punctuation: / % $ : ' " + & ? ! @ # * ; < > =
    return re.sub(r'[^\w\s,.\-\(\)\[\]/\%\$\:\'\"\+\&\?\!\@\#\*\;\<\>\=\u0600-\u06FF]', '', text)

def fix_arabic(text):
    """
    Fixes Arabic text rendering in PDFs:
    1. Reshapes letters (connects them).
    2. Reverses direction (Right-to-Left).
    """
    if pd.isna(text): return "N/A"
    text = str(text)
    
    # Remove emojis first
    text = remove_emojis(text)
    
    try:
        # Check if text contains Arabic characters
        if any('\u0600' <= char <= '\u06FF' for char in text):
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        return text
    except:
        return text


