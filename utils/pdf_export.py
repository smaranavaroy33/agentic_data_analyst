import os
import tempfile
from io import BytesIO
import re
import pandas as pd
import plotly.express as px

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Preformatted
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch

def generate_insights_pdf(analysis_history):
    """
    Generates a PDF document from the analysis history, including text and generated Plotly charts.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=72, leftMargin=72,
        topMargin=72, bottomMargin=72
    )
    
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'MainTitle',
        parent=styles['Title'],
        fontSize=24,
        spaceAfter=30
    )
    heading_style = ParagraphStyle(
        'QuestionHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor='#1f77b4',
        spaceAfter=10
    )
    normal_style = styles['Normal']
    code_style = ParagraphStyle(
        'Code',
        parent=styles['Code'],
        backColor='#f4f4f4',
        borderPadding=5,
        wordWrap='CJK',
        spaceAfter=10
    )
    
    elements = []
    
    # Add Title
    elements.append(Paragraph("Data Analysis Insights", title_style))
    elements.append(Spacer(1, 0.25 * inch))
    
    temp_files = [] # Keep track of temporary image files to delete later
    
    for i, entry in enumerate(analysis_history):
        # 1. Question (Heading)
        elements.append(Paragraph(f"Q{i+1}: {entry['question']}", heading_style))
        
        # 2. SQL Query
        sql_query = entry.get('sql_query', '')
        if sql_query:
            elements.append(Paragraph("<b>Executed SQL Query:</b>", normal_style))
            elements.append(Preformatted(sql_query, code_style))
        
        # 3. Summary / Insights
        summary = entry.get('summary', '')
        if summary:
            elements.append(Paragraph("<b>Insights:</b>", normal_style))
            
            # Format markdown bold text for ReportLab
            formatted_summary = summary.replace('\n', '<br/>')
            formatted_summary = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', formatted_summary)
            
            elements.append(Paragraph(formatted_summary, normal_style))
            elements.append(Spacer(1, 0.1 * inch))
        
        # 4. Chart Generation
        needs_chart = entry.get('needs_chart', False)
        plotly_code = entry.get('plotly_code', '')
        raw_data = entry.get('raw_data', [])
        
        if needs_chart and plotly_code:
            try:
                # Re-execute code to generate the figure object
                scope = {"pd": pd, "px": px, "data": raw_data}
                exec(plotly_code, {}, scope)
                
                if "fig" in scope:
                    fig = scope["fig"]
                    
                    # Save to a temporary PNG file
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.png')
                    # kaleido engine is required to export plotly to static images
                    fig.write_image(temp_file.name, engine="kaleido", width=800, height=500)
                    temp_files.append(temp_file.name)
                    
                    # Add image to PDF document
                    img = Image(temp_file.name, width=6*inch, height=3.75*inch)
                    elements.append(img)
            except Exception as e:
                elements.append(Paragraph(f"<i>[Chart Generation Error: {str(e)}]</i>", normal_style))
                
        # Add spacing between historical entries
        elements.append(Spacer(1, 0.4 * inch))
        
    # Build the PDF
    doc.build(elements)
    
    # Cleanup temporary image files
    for tf in temp_files:
        try:
            os.remove(tf)
        except Exception:
            pass
            
    buffer.seek(0)
    return buffer.getvalue()