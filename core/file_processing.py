import os
import json
import logging
from typing import Optional
from pathlib import Path

# Third-party libraries
try:
    import PyPDF2
    from docx import Document
    import lxml.etree as ET
except ImportError:
    # Fallback for missing dependencies
    PyPDF2 = None
    Document = None
    ET = None

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class FileProcessor:
    """Process various file formats to extract text content for AI processing"""
    
    def __init__(self):
        self.supported_formats = {
            '.pdf': self._process_pdf,
            '.docx': self._process_docx,
            '.xml': self._process_xml,
            '.json': self._process_json,
            '.md': self._process_markdown,
            '.txt': self._process_text,
        }
    
    def process_file(self, file_path: str) -> str:
        """
        Process a file and extract its text content
        
        Args:
            file_path (str): Path to the file to process
            
        Returns:
            str: Extracted text content
            
        Raises:
            ValueError: If file format is not supported
            Exception: For any processing errors
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_ext = Path(file_path).suffix.lower()
        
        if file_ext not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_ext}. Supported formats: {list(self.supported_formats.keys())}")
        
        logger.info(f"Processing file: {file_path} with format: {file_ext}")
        
        try:
            processor = self.supported_formats[file_ext]
            content = processor(file_path)
            logger.info(f"Successfully processed file: {file_path}")
            return content
        except Exception as e:
            logger.error(f"Error processing file {file_path}: {e}")
            raise
    
    def _process_pdf(self, file_path: str) -> str:
        """Extract text from PDF files"""
        if PyPDF2 is None:
            raise ImportError("PyPDF2 is required for PDF processing. Install with: pip install PyPDF2")
        
        text = ""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"PDF processing error: {e}")
            raise
    
    def _process_docx(self, file_path: str) -> str:
        """Extract text from DOCX files"""
        if Document is None:
            raise ImportError("python-docx is required for DOCX processing. Install with: pip install python-docx")
        
        try:
            doc = Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text.strip()
        except Exception as e:
            logger.error(f"DOCX processing error: {e}")
            raise
    
    def _process_xml(self, file_path: str) -> str:
        """Extract text from XML files"""
        if ET is None:
            raise ImportError("lxml is required for XML processing. Install with: pip install lxml")
        
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            # Extract all text content from XML elements
            text = ET.tostring(root, method='text', encoding='unicode')
            return text.strip()
        except Exception as e:
            logger.error(f"XML processing error: {e}")
            raise
    
    def _process_json(self, file_path: str) -> str:
        """Extract text from JSON files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
                # Convert JSON to readable text
                text = json.dumps(data, indent=2, ensure_ascii=False)
                return text
        except Exception as e:
            logger.error(f"JSON processing error: {e}")
            raise
    
    def _process_markdown(self, file_path: str) -> str:
        """Extract text from Markdown files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return content
        except Exception as e:
            logger.error(f"Markdown processing error: {e}")
            raise
    
    def _process_text(self, file_path: str) -> str:
        """Extract text from plain text files"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                return content
        except Exception as e:
            logger.error(f"Text file processing error: {e}")
            raise
    
    def get_supported_formats(self) -> list:
        """Get list of supported file formats"""
        return list(self.supported_formats.keys())
    
    def validate_file_size(self, file_path: str, max_size_mb: int = 10) -> bool:
        """
        Validate file size against maximum allowed size
        
        Args:
            file_path (str): Path to the file
            max_size_mb (int): Maximum size in MB
            
        Returns:
            bool: True if file size is within limits
        """
        file_size = os.path.getsize(file_path)
        max_size_bytes = max_size_mb * 1024 * 1024
        
        if file_size > max_size_bytes:
            raise ValueError(f"File size ({file_size / (1024*1024):.2f} MB) exceeds maximum allowed size ({max_size_mb} MB)")
        
        return True
    
    def extract_metadata(self, file_path: str) -> dict:
        """
        Extract basic metadata from the file
        
        Args:
            file_path (str): Path to the file
            
        Returns:
            dict: File metadata
        """
        file_stat = os.stat(file_path)
        return {
            'filename': os.path.basename(file_path),
            'file_size': file_stat.st_size,
            'file_format': Path(file_path).suffix.lower(),
            'created': file_stat.st_ctime,
            'modified': file_stat.st_mtime,
        }


# Utility function for standalone use
def process_file(file_path: str) -> str:
    """
    Utility function to process a file without instantiating the class
    
    Args:
        file_path (str): Path to the file
        
    Returns:
        str: Extracted text content
    """
    processor = FileProcessor()
    return processor.process_file(file_path)
