from fpdf import FPDF
import os
import glob
import pandas as pd
import platform
import arabic_reshaper
from bidi.algorithm import get_display

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

def fix_arabic(text):
    """
    Fixes Arabic text rendering in PDFs:
    1. Reshapes letters (connects them).
    2. Reverses direction (Right-to-Left).
    """
    if pd.isna(text): return "N/A"
    text = str(text)
    
    try:
        # Check if text contains Arabic characters
        if any('\u0600' <= char <= '\u06FF' for char in text):
            reshaped_text = arabic_reshaper.reshape(text)
            bidi_text = get_display(reshaped_text)
            return bidi_text
        return text
    except:
        return text

def compile_final_pdf(idea_name):
    print(f"\n📄 [Tool 9] Compiling Professional PDF Report...")
    
    pdf = PDFReport()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    # --- CROSS-PLATFORM FONT LOADING ---
    system_name = platform.system()
    font_path = None
    if system_name == "Windows":
        font_path = r"C:\Windows\Fonts\arial.ttf"
    elif system_name == "Darwin": # Mac
        font_path = "/Library/Fonts/Arial.ttf"
    elif system_name == "Linux":
        font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

    try:
        if font_path and os.path.exists(font_path):
            pdf.add_font("ArialUnicode", style="", fname=font_path)
            pdf.add_font("ArialUnicode", style="B", fname=font_path)
            print(f"   ✅ Loaded System Font: {font_path}")
        else:
            print("   ⚠️ Custom font not found. Arabic may not render correctly.")
    except Exception as e:
        print(f"   ⚠️ Font Error: {e}")

    # --- PAGE 1: TITLE & EXECUTIVE SUMMARY ---
    pdf.add_page()
    pdf.set_font_for_content('B', 24)
    pdf.cell(0, 20, f"Market Research: {fix_arabic(idea_name)}", 0, 1, 'C')
    pdf.ln(10)
    
    # Read Report
    report_text = "No report text found."
    if os.path.exists("data_output/FINAL_MARKET_REPORT.md"):
        with open("data_output/FINAL_MARKET_REPORT.md", "r", encoding="utf-8") as f:
            raw_text = f.read()
            report_text = raw_text.replace("**", "").replace("##", "").replace("###", "").replace("---", "")
    
    pdf.chapter_title("Executive Summary")
    pdf.chapter_body(fix_arabic(report_text[:2000] + "..."))
    
    # --- PAGE 2: MARKET DEMAND ---
    pdf.add_page()
    pdf.chapter_title("Market Validation & Trends")
    pdf.add_image_centered("data_output/market_demand_chart.png")
    pdf.chapter_body("Analysis of market interest over the last 12 months.")
    
    # --- PAGE 3: FINANCIALS ---
    pdf.add_page()
    pdf.chapter_title("Financial Feasibility")
    pdf.cell(0, 10, "1. Startup Cost Estimates", 0, 1, 'L')
    pdf.add_image_centered("data_output/finance_startup_pie.png")
    
    pdf.add_page()
    pdf.chapter_title("Profitability Projections")
    pdf.cell(0, 10, "2. Break-Even Analysis", 0, 1, 'L')
    pdf.add_image_centered("data_output/finance_breakeven_line.png")

    # ... inside compile_final_pdf ...

    # --- PAGE 4: COMPETITOR FEATURES ---
    pdf.add_page()
    pdf.chapter_title("Competitor Feature Analysis")
    
    comp_files = glob.glob("data_output/*_competitors.csv")
    if comp_files:
        try:
            df = pd.read_csv(comp_files[0])
            
            pdf.set_font_for_content('B', 10)
            # Adjusted Widths: Name (50), Features (140)
            pdf.cell(50, 10, 'Competitor', 1)
            pdf.cell(140, 10, 'Key Features Identified', 1)
            pdf.ln()
            
            pdf.set_font_for_content('', 9)
            for _, row in df.head(8).iterrows():
                name = fix_arabic(row.get('Name', 'N/A'))[:25]
                # Grab the NEW 'Features' column
                features = fix_arabic(row.get('Features', row.get('Snippet', 'N/A')))[:110].replace("\n", " ")
                
                pdf.cell(50, 10, name, 1)
                pdf.cell(140, 10, features, 1)
                pdf.ln()
        except Exception as e:
            print(f"   ⚠️ Error adding table: {e}")

if __name__ == "__main__":
    compile_final_pdf("Dating App in Cairo")