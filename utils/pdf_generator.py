import os
import io
from datetime import datetime
from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT

class PDFGenerator:
    def __init__(self, app_root):
        self.app_root = app_root
        
    def generate_pdf(self, data):
        """Generate PDF from report data using reportlab"""
        try:
            # Create PDF buffer
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4, rightMargin=72, leftMargin=72, topMargin=72, bottomMargin=72)
            
            # Get styles
            styles = getSampleStyleSheet()
            title_style = ParagraphStyle(
                'CustomTitle',
                parent=styles['Heading1'],
                fontSize=24,
                spaceAfter=30,
                alignment=TA_CENTER,
                textColor=colors.darkblue
            )
            
            heading_style = ParagraphStyle(
                'CustomHeading',
                parent=styles['Heading2'],
                fontSize=16,
                spaceAfter=12,
                textColor=colors.darkblue
            )
            
            normal_style = styles['Normal']
            
            # Build story (content)
            story = []
            
            # Title page
            brand_name = data.get("brand_config", {}).get("name", "Unknown Brand")
            industry = data.get("brand_config", {}).get("industry", "Unknown Industry")
            
            story.append(Paragraph(f"AI Brand Intelligence Report", title_style))
            story.append(Spacer(1, 20))
            story.append(Paragraph(f"<b>{brand_name}</b>", heading_style))
            story.append(Paragraph(f"Industry: {industry}", normal_style))
            story.append(Spacer(1, 30))
            story.append(Paragraph(f"Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}", normal_style))
            story.append(PageBreak())
            
            # Executive Summary
            story.append(Paragraph("Executive Summary", heading_style))
            story.append(Spacer(1, 12))
            
            # Key metrics table
            analysis = data.get("analysis", {})
            metrics_data = [
                ["Metric", "Value"],
                ["Total Queries Analyzed", str(analysis.get('total_responses', 0))],
                ["Total Brand Mentions", str(analysis.get('total_mentions', 0))],
                ["Organic Mentions", str(analysis.get('total_organic_mentions', 0))],
                ["Organic Mention Rate", f"{(analysis.get('organic_mention_rate', 0) * 100):.1f}%"]
            ]
            
            metrics_table = Table(metrics_data, colWidths=[3*inch, 2*inch])
            metrics_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(metrics_table)
            story.append(Spacer(1, 20))
            
            # Key insight
            organic_rate = analysis.get('organic_mention_rate', 0)
            if organic_rate == 0:
                insight = f"No organic visibility detected. Your brand doesn't appear when users ask generic questions about {industry}. This suggests limited AI search authority."
            elif organic_rate < 0.1:
                insight = f"Low organic visibility ({(organic_rate * 100):.1f}%). Your brand occasionally appears in category searches, but there's significant room for improvement."
            else:
                insight = f"Good organic visibility ({(organic_rate * 100):.1f}%)! Your brand appears when users explore the category without mentioning you directly."
            
            story.append(Paragraph(f"<b>Key Insight:</b> {insight}", normal_style))
            story.append(PageBreak())
            
            # Platform Performance
            story.append(Paragraph("Platform Performance", heading_style))
            story.append(Spacer(1, 12))
            
            ai_responses = data.get("ai_responses", {})
            for platform, responses in ai_responses.items():
                if not responses:
                    continue
                    
                # Calculate metrics
                total_mentions = sum(r.get('analysis', {}).get('mentions_found', 0) for r in responses if r.get('analysis'))
                organic_mentions = sum(r.get('analysis', {}).get('mentions_found', 0) for r in responses if r.get('analysis', {}).get('organic_mention'))
                sentiment_scores = [r.get('analysis', {}).get('sentiment_score', 0) for r in responses if r.get('analysis')]
                avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
                
                platform_data = [
                    ["Metric", "Value"],
                    ["Responses", str(len(responses))],
                    ["Total Mentions", str(total_mentions)],
                    ["Organic Mentions", str(organic_mentions)],
                    ["Organic Rate", f"{(organic_mentions / len(responses) * 100):.1f}%" if responses else "0%"],
                    ["Avg Sentiment", f"{avg_sentiment:.2f}"]
                ]
                
                story.append(Paragraph(f"<b>{platform.upper()}</b>", normal_style))
                platform_table = Table(platform_data, colWidths=[2*inch, 1.5*inch])
                platform_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.lightgrey),
                    ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(platform_table)
                story.append(Spacer(1, 12))
            
            story.append(PageBreak())
            
            # Strategic Recommendations
            story.append(Paragraph("Strategic Recommendations", heading_style))
            story.append(Spacer(1, 12))
            
            recommendations = data.get('recommendations', {}).get('recommendations', [])
            if recommendations:
                for i, rec in enumerate(recommendations[:5], 1):
                    story.append(Paragraph(f"<b>{i}. {rec.get('action', 'No action specified')}</b>", normal_style))
                    story.append(Paragraph(f"Priority: {rec.get('priority', 'medium').upper()}", normal_style))
                    story.append(Paragraph(f"Rationale: {rec.get('rationale', 'No rationale provided')}", normal_style))
                    story.append(Spacer(1, 12))
            else:
                # Default recommendations based on organic mention rate
                if organic_rate == 0:
                    story.append(Paragraph("1. <b>Critical:</b> Create authoritative content for category exploration queries. You need to establish thought leadership in your industry.", normal_style))
                    story.append(Paragraph("2. <b>High Priority:</b> Develop comprehensive FAQ content that answers common questions in your field.", normal_style))
                    story.append(Paragraph("3. <b>Medium Priority:</b> Build industry expertise content that AI systems can reference.", normal_style))
                elif organic_rate < 0.1:
                    story.append(Paragraph("1. <b>High Priority:</b> Expand content marketing to cover more category-based topics.", normal_style))
                    story.append(Paragraph("2. <b>Medium Priority:</b> Create educational content positioning you as an industry authority.", normal_style))
                else:
                    story.append(Paragraph("1. <b>Maintain:</b> Continue your content strategy as you have good organic visibility!", normal_style))
            
            # Build PDF
            doc.build(story)
            buffer.seek(0)
            return buffer.getvalue()
            
        except Exception as e:
            raise Exception(f"Error generating PDF: {str(e)}")
    
    def get_filename(self, brand_name):
        """Generate filename for the PDF"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_brand_name = "".join(c for c in brand_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
        safe_brand_name = safe_brand_name.replace(' ', '_')
        return f"{safe_brand_name}_brand_report_{timestamp}.pdf" 