import os
import glob
import pandas as pd
import platform
import arabic_reshaper
from bidi.algorithm import get_display
from fpdf import FPDF
from app.core.config import settings, gemini_client
from app.graph.market_research_agent import prompts
from app.core.config import settings, gemini_client
from app.graph.market_research_agent import prompts
from app.graph.market_research_agent.logger_config import get_logger
import json
import asyncio
import re

logger = get_logger("PDFUtils")

def generate_report(file_path: str, query: str, trend_file=None, finance_file=None):
    logger.info(f"\n📝 [Tool 5] Synthesizing Data & Calculating Opportunity Score...")
    
    pain_score = 0
    val_data = ""
    if os.path.exists(file_path):
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
    
    prompt = prompts.investment_memo_prompt(query, pain_score, growth_pct, grade, opp_score, finance_summary, val_data)
    try:
        res = gemini_client.models.generate_content(model=settings.GEMINI_MODEL_NAME, contents=prompt)
        with open("data_output/FINAL_MARKET_REPORT.md", "w", encoding="utf-8") as f: f.write(res.text)
        logger.info(f"✅ Final Report Saved.")
    except Exception as e: logger.error(f"⚠️ Report Error: {e}")

class PDFReport(FPDF):
    def header(self):
        self.set_font_for_content('B', 12)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, 'Spark2Scale AI - Market Research Report', 0, 1, 'R')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Arial", 'I', 8)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, label):
        self.set_font_for_content('B', 16)
        self.set_text_color(0, 50, 100)
        self.cell(0, 10, label, 0, 1, 'L')
        self.ln(2)
        self.set_draw_color(0, 50, 100)
        self.line(10, self.get_y(), 200, self.get_y())
        self.ln(5)

    def chapter_body(self, text):
        self.set_font_for_content('', 11)
        self.set_text_color(0, 0, 0)
        self.multi_cell(0, 6, text)
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
        # Always try to use the Unicode font first
        try:
            self.set_font('ArialUnicode', style, size)
        except:
            self.set_font('Arial', style, size)

def remove_emojis(text):
    if not isinstance(text, str): return text
    # Remove emojis using regex (range of emojis)
    # This is a basic regex for common emojis
    return re.sub(r'[^\w\s,.\-\(\)\[\]\u0600-\u06FF]', '', text)

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


