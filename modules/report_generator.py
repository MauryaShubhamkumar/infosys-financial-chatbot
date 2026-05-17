import os
import pandas as pd
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime
import re
from xml.sax.saxutils import escape

OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

def generate_pdf(content: str, filename: str) -> str:
    """Generates a PDF report from text content and returns the file path."""
    if not filename.endswith(".pdf"):
        filename += ".pdf"
    
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    doc = SimpleDocTemplate(filepath, pagesize=letter)
    styles = getSampleStyleSheet()
    Story = []
    
    # Title
    Story.append(Paragraph(f"Financial Analyst Report - {datetime.now().strftime('%Y-%m-%d')}", styles['Title']))
    Story.append(Spacer(1, 12))
    
    # Parse text into paragraphs and headers
    for text_block in content.split("\n\n"):
        text_block = text_block.strip()
        if not text_block:
            continue
            
        # Determine style based on markdown headers
        style = styles['Normal']
        if text_block.startswith("### "):
            style = styles['Heading3']
            text_block = text_block[4:]
        elif text_block.startswith("## "):
            style = styles['Heading2']
            text_block = text_block[3:]
        elif text_block.startswith("# "):
            style = styles['Heading1']
            text_block = text_block[2:]
            
        # Escape XML special characters
        text_block = escape(text_block)
        # Replace markdown bold with reportlab bold tags
        text_block = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text_block)
        
        try:
            p = Paragraph(text_block, style)
            Story.append(p)
            Story.append(Spacer(1, 12))
        except Exception:
            # Fallback if XML parsing fails
            p = Paragraph(text_block.replace("<", "").replace(">", ""), style)
            Story.append(p)
            Story.append(Spacer(1, 12))
                
    doc.build(Story)
    return filepath

def generate_excel(data: list, filename: str) -> str:
    """Generates an Excel file from a list of dictionaries and returns the file path."""
    if not filename.endswith(".xlsx"):
        filename += ".xlsx"
        
    filepath = os.path.join(OUTPUT_DIR, filename)
    
    df = pd.DataFrame(data)
    df.to_excel(filepath, index=False)
    
    return filepath
