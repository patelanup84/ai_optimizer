#!/usr/bin/env python3
"""
Simple test script for PDF generation functionality
"""

import os
import sys

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from utils.pdf_generator import PDFGenerator
    
    # Test data
    test_data = {
        "brand_config": {
            "name": "Test Brand",
            "industry": "Technology"
        },
        "analysis": {
            "total_mentions": 42,
            "total_responses": 100,
            "organic_mention_rate": 0.15,
            "total_organic_mentions": 15
        },
        "ai_responses": {
            "chatgpt": [
                {
                    "analysis": {
                        "mentions_found": 20,
                        "organic_mention": True,
                        "sentiment_score": 0.5
                    }
                }
            ]
        }
    }
    
    # Initialize PDF generator
    pdf_gen = PDFGenerator(os.getcwd())
    
    # Generate PDF
    print("Generating PDF...")
    pdf_content = pdf_gen.generate_pdf(test_data)
    
    # Save test PDF
    filename = pdf_gen.get_filename("Test Brand")
    with open(filename, 'wb') as f:
        f.write(pdf_content)
    
    print(f"✅ PDF generated successfully: {filename}")
    print(f"📄 PDF size: {len(pdf_content)} bytes")
    
    # Verify it's a valid PDF
    if pdf_content.startswith(b'%PDF'):
        print("✅ Valid PDF format confirmed")
    else:
        print("❌ Invalid PDF format")
        
except ImportError as e:
    print(f"❌ Import error: {e}")
    print("Make sure to install dependencies: pip install -r requirements.txt")
except Exception as e:
    print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("Testing PDF generation functionality...") 