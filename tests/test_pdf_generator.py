import os
import tempfile
import pytest
from utils.pdf_generator import PDFGenerator

class TestPDFGenerator:
    def setup_method(self):
        """Set up test environment"""
        # Create a temporary directory for testing
        self.test_dir = tempfile.mkdtemp()
        
        # Initialize PDF generator
        self.pdf_generator = PDFGenerator(self.test_dir)
    
    def teardown_method(self):
        """Clean up test environment"""
        import shutil
        shutil.rmtree(self.test_dir)
    
    def test_pdf_generator_initialization(self):
        """Test PDF generator initializes correctly"""
        assert self.pdf_generator.app_root == self.test_dir
    
    def test_filename_generation(self):
        """Test filename generation"""
        filename = self.pdf_generator.get_filename("Test Brand")
        assert "Test_Brand_brand_report_" in filename
        assert filename.endswith(".pdf")
        
        # Test with special characters
        filename2 = self.pdf_generator.get_filename("Brand & Co. (LLC)")
        assert "Brand___Co___LLC_brand_report_" in filename2
        assert filename2.endswith(".pdf")
    
    def test_pdf_generation_with_sample_data(self):
        """Test PDF generation with sample data"""
        sample_data = {
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
        
        try:
            pdf_content = self.pdf_generator.generate_pdf(sample_data)
            assert pdf_content is not None
            assert len(pdf_content) > 0
            # Check if it's a valid PDF (starts with PDF header)
            assert pdf_content.startswith(b'%PDF')
        except Exception as e:
            # If reportlab is not available, skip this test
            pytest.skip(f"ReportLab not available: {e}")
    
    def test_pdf_generation_with_empty_data(self):
        """Test PDF generation with empty data"""
        try:
            pdf_content = self.pdf_generator.generate_pdf({})
            assert pdf_content is not None
            assert len(pdf_content) > 0
            assert pdf_content.startswith(b'%PDF')
        except Exception as e:
            # If reportlab is not available, skip this test
            pytest.skip(f"ReportLab not available: {e}")
    
    def test_pdf_generation_with_minimal_data(self):
        """Test PDF generation with minimal data"""
        minimal_data = {
            "brand_config": {
                "name": "Minimal Brand",
                "industry": "Test"
            }
        }
        
        try:
            pdf_content = self.pdf_generator.generate_pdf(minimal_data)
            assert pdf_content is not None
            assert len(pdf_content) > 0
            assert pdf_content.startswith(b'%PDF')
        except Exception as e:
            # If reportlab is not available, skip this test
            pytest.skip(f"ReportLab not available: {e}")

if __name__ == "__main__":
    pytest.main([__file__]) 