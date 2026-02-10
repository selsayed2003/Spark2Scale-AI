import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.graphics.shapes import Drawing, Rect, String, Line
from reportlab.graphics.charts.spider import SpiderChart
from reportlab.lib.enums import TA_JUSTIFY

# --- 1. BRAND PALETTE ---
COLOR_PRIMARY = colors.HexColor("#576238")  # Olive Green
COLOR_ACCENT = colors.HexColor("#ffd95d")   # Mustard Yellow
COLOR_BG = colors.HexColor("#F0EADC")       # Cream
COLOR_TEXT = colors.HexColor("#2c3e50")     # Dark Grey
COLOR_LIGHT_TEXT = colors.HexColor("#5f6368")
COLOR_RISK = colors.HexColor("#c0392b")     # Professional Red

# --- 2. DATA HELPERS ---

def clean_score(score_input):
    """Converts '3.0/5' or '3' or None to a float."""
    try:
        if score_input is None: return 0.0
        s = str(score_input)
        if "/" in s: s = s.split("/")[0]
        return float(s)
    except:
        return 0.0

def get_agent_data(data):
    """Extracts scores for the Radar Chart."""
    mapping = {
        "Team": "team_report",
        "Problem": "problem_report",
        "Market": "market_report",
        "Traction": "traction_report",
        "Business": "business_report",
        "GTM": "gtm_report",
        "Vision": "vision_report",
        "Ops": "operations_report",
        "Product": "product_report"
    }
    
    labels = []
    scores = []
    
    for label, key in mapping.items():
        if key in data:
            labels.append(label)
            # Default to 0.1 instead of 0 for radar visibility if empty
            val = clean_score(data[key].get("score"))
            scores.append(val if val > 0 else 0.1)
            
    return labels, scores

# --- 3. GRAPHICS GENERATORS ---

def draw_radar_chart(labels, scores):
    """Generates the Spider/Radar chart."""
    if not scores: return Drawing(10, 10) # Fallback empty drawing
    
    width = 400
    height = 250
    d = Drawing(width, height)
    
    chart = SpiderChart()
    chart.x = 50
    chart.y = 20
    chart.width = 300
    chart.height = 200
    chart.data = [scores] 
    chart.labels = labels
    chart.strands.strokeColor = colors.white
    chart.fillColor = colors.Color(0.34, 0.38, 0.22, 0.2) 
    chart.strands.strokeWidth = 1
    chart.spokes.strokeColor = colors.lightgrey
    chart.strandLabels.fontName = "Helvetica"
    chart.strandLabels.fontSize = 8
    
    # Marker styling (Outer line)
    chart.strands[0].strokeColor = COLOR_PRIMARY
    chart.strands[0].strokeWidth = 2
    chart.strands[0].fillColor = colors.Color(0.34, 0.38, 0.22, 0.4)
    
    d.add(chart)
    return d

def draw_score_bar(score, max_score=5):
    """Draws a horizontal progress bar."""
    width = 150
    height = 12
    d = Drawing(width, height)
    
    # Background
    d.add(Rect(0, 0, width, height, fillColor=colors.whitesmoke, strokeColor=None, rx=3, ry=3))
    
    # Fill
    pct = min(max(score / max_score, 0), 1)
    fill_width = width * pct
    
    # Color Logic
    if score < 2: c = COLOR_RISK
    elif score < 4: c = COLOR_ACCENT
    else: c = COLOR_PRIMARY
    
    if fill_width > 0:
        d.add(Rect(0, 0, fill_width, height, fillColor=c, strokeColor=None, rx=3, ry=3))
    
    # Text
    d.add(String(width + 10, 2, f"{score}/5.0", fontName="Helvetica-Bold", fontSize=9, fillColor=COLOR_TEXT))
    return d

def draw_separator_line(width, color=colors.lightgrey):
    """Draws a line wrapped in a Drawing object (Fixes wrapOn error)"""
    d = Drawing(width, 5) # Height 5 to give a bit of buffer
    d.add(Line(0, 0, width, 0, strokeColor=color, strokeWidth=1))
    return d

# --- 4. LAYOUT COMPONENTS ---

def header_footer(canvas, doc):
    canvas.saveState()
    
    # --- HEADER ---
    canvas.setFillColor(COLOR_PRIMARY)
    canvas.rect(0, LETTER[1] - 40, LETTER[0], 40, fill=1, stroke=0)
    
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 10)
    canvas.drawString(0.5 * inch, LETTER[1] - 25, "SPARK2SCALE | AI EVALUATION")
    
    canvas.setFont("Helvetica", 9)
    canvas.drawRightString(8.0 * inch, LETTER[1] - 25, "CONFIDENTIAL REPORT")
    
    # --- FOOTER ---
    canvas.setFillColor(COLOR_BG)
    canvas.rect(0, 0, LETTER[0], 40, fill=1, stroke=0)
    
    canvas.setFillColor(COLOR_PRIMARY)
    canvas.setFont("Helvetica", 8)
    canvas.drawString(0.5 * inch, 0.25 * inch, "Methodology: YC Frameworks, Berkus Method, Live Market Search")
    canvas.drawRightString(8.0 * inch, 0.25 * inch, f"Page {doc.page}")
    
    canvas.restoreState()

# --- 5. MAIN REPORT GENERATOR ---

def generate_pdf_report(json_data: dict, filename: str):
    doc = SimpleDocTemplate(
        filename, 
        pagesize=LETTER, 
        topMargin=60, 
        bottomMargin=50,
        leftMargin=50,
        rightMargin=50
    )
    
    styles = getSampleStyleSheet()
    
    # --- CUSTOM STYLES ---
    style_hero = ParagraphStyle('Hero', parent=styles['Heading1'], fontName='Helvetica-Bold', fontSize=28, textColor=COLOR_PRIMARY, spaceAfter=5)
    style_subhero = ParagraphStyle('SubHero', parent=styles['Normal'], fontName='Helvetica', fontSize=14, textColor=COLOR_LIGHT_TEXT, spaceAfter=20)
    
    style_h2 = ParagraphStyle('H2', parent=styles['Heading2'], fontName='Helvetica-Bold', fontSize=14, textColor=COLOR_PRIMARY, spaceBefore=15, spaceAfter=10)
    
    style_body = ParagraphStyle('Body', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=COLOR_TEXT, leading=14, spaceAfter=6, alignment=TA_JUSTIFY)
    
    style_flag = ParagraphStyle('Flag', parent=styles['Normal'], fontName='Helvetica', fontSize=9, textColor=COLOR_TEXT, leftIndent=15, bulletIndent=5, spaceAfter=2)

    story = []
    
    # ==========================
    # PAGE 1: EXECUTIVE SUMMARY
    # ==========================
    
    # 1. Title Block
    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("Startup Valuation & Readiness Report", style_hero))
    story.append(Paragraph("Prepared by Spark2Scale AI Council", style_subhero))
    story.append(Spacer(1, 0.2*inch))
    
    # 2. Methodology
    method_text = """
    <b>Evaluation Methodology:</b> This report aggregates intelligence from 9 specialized AI Agents. 
    We utilize forensic data analysis, <b>Y Combinator</b> investment frameworks, the <b>Berkus Method</b> for early-stage valuation, 
    and live <b>DuckDuckGo/Google Search</b> verification to provide a rigorous, objective assessment.
    """
    t_method = Table([[Paragraph(method_text, style_body)]], colWidths=[7*inch])
    t_method.setStyle(TableStyle([
        ('LINEBELOW', (0,0), (-1,-1), 2, COLOR_ACCENT),
        ('PADDING', (0,0), (-1,-1), 10)
    ]))
    story.append(t_method)
    story.append(Spacer(1, 0.3*inch))
    
    # 3. Radar Chart & Stats
    labels, scores = get_agent_data(json_data)
    radar = draw_radar_chart(labels, scores)
    
    # Stats logic
    valid_scores = [s for s in scores if s > 0]
    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else 0
    top_strength = labels[scores.index(max(scores))] if scores else "N/A"
    crit_gap = labels[scores.index(min(scores))] if scores else "N/A"
    
    stats_content = [
        [Paragraph("<b>OVERALL READINESS</b>", style_body)],
        [Paragraph(f"<font size=24 color={COLOR_PRIMARY}><b>{avg_score:.1f}/5.0</b></font>", style_body)],
        [Spacer(1, 10)],
        [Paragraph(f"<b>Top Strength:</b> {top_strength}", style_body)],
        [Paragraph(f"<b>Critical Gap:</b> {crit_gap}", style_body)],
        [Spacer(1, 10)],
        [Paragraph("<i>Scores < 2.0 indicate structural risks requiring pivots.</i>", style_flag)]
    ]
    
    t_dashboard = Table([
        [radar, Table(stats_content)]
    ], colWidths=[4*inch, 2.5*inch])
    
    t_dashboard.setStyle(TableStyle([
        ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
        ('ALIGN', (0,0), (0,0), 'CENTER')
    ]))
    story.append(t_dashboard)
    story.append(PageBreak())

    # ==========================
    # PAGES 2+: AGENT DEEP DIVES
    # ==========================
    
    agent_order = [
        ("Team & Founders", "team_report", "The Execution Engine"),
        ("Problem Definition", "problem_report", "Market Need Validation"),
        ("Market & Strategy", "market_report", "Scalability & Moats"),
        ("Traction & Velocity", "traction_report", "Proof of Demand"),
        ("Business Model", "business_report", "Unit Economics & Viability"),
        ("Go-To-Market", "gtm_report", "Acquisition Strategy"),
        ("Product Status", "product_report", "Technical Readiness"),
        ("Operations", "operations_report", "Fundraising Hygiene")
    ]

    for friendly_name, key, tagline in agent_order:
        if key not in json_data: continue
        
        report = json_data[key]
        score = clean_score(report.get("score"))
        
        # --- CARD CONTAINER ---
        elements = []
        
        # 1. Header Table
        header_table_data = [
            [Paragraph(f"<b>{friendly_name.upper()}</b>", style_h2), draw_score_bar(score)],
            [Paragraph(f"<i>{tagline}</i>", style_flag), ""]
        ]
        t_header = Table(header_table_data, colWidths=[4.5*inch, 2*inch])
        t_header.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('ALIGN', (1,0), (1,1), 'RIGHT'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 0)
        ]))
        elements.append(t_header)
        elements.append(Spacer(1, 5))
        
        # --- FIX: Use helper instead of raw Line ---
        elements.append(draw_separator_line(6.5*inch, colors.lightgrey))
        elements.append(Spacer(1, 10))
        
        # 2. Main Analysis
        raw_text = report.get("explanation", "Data pending integration.")
        # Friendly cleanup
        friendly_text = raw_text.replace("Impossible", "Challenging").replace("Ghost Town", "Pre-Traction Phase").replace("Bankruptcy", "Financial Risk")
        
        elements.append(Paragraph(friendly_text, style_body))
        elements.append(Spacer(1, 10))
        
        # 3. Key Findings (Grid)
        reds = report.get("red_flags", []) or report.get("key_weaknesses", [])
        greens = report.get("green_flags", []) or report.get("key_strengths", [])
        
        red_text = "<b>⚠️ ATTENTION NEEDED:</b><br/>" + "<br/>".join([f"• {r}" for r in reds[:3]]) if reds else "No critical flags."
        green_text = "<b>✅ VALIDATED STRENGTHS:</b><br/>" + "<br/>".join([f"• {g}" for g in greens[:3]]) if greens else "Strengths developing..."
        
        t_flags = Table([
            [Paragraph(red_text, style_body), Paragraph(green_text, style_body)]
        ], colWidths=[3.25*inch, 3.25*inch])
        
        t_flags.setStyle(TableStyle([
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('BACKGROUND', (0,0), (0,0), colors.Color(0.9, 0.3, 0.2, 0.05)), 
            ('BACKGROUND', (1,0), (1,0), colors.Color(0.34, 0.38, 0.22, 0.05)),
            ('PADDING', (0,0), (-1,-1), 8),
            ('GRID', (0,0), (-1,-1), 0.5, colors.white)
        ]))
        elements.append(t_flags)
        elements.append(Spacer(1, 20))
        
        story.append(KeepTogether(elements))

    doc.build(story, onFirstPage=header_footer, onLaterPages=header_footer)