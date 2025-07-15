import PyPDF2
import docx
import os
import tempfile
from typing import Dict, List, Optional
import streamlit as st

class DocumentProcessor:
    """Handles PDF and document processing for chapter extraction"""
    
    def __init__(self):
        self.supported_formats = ['.pdf', '.docx', '.txt']
    
    def extract_text_from_pdf(self, file_path: str) -> str:
        """Extract text from PDF file"""
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                text = ""
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
                return text
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return ""
    
    def extract_text_from_docx(self, file_path: str) -> str:
        """Extract text from DOCX file"""
        try:
            doc = docx.Document(file_path)
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading DOCX: {str(e)}")
            return ""
    
    def extract_text_from_txt(self, file_path: str) -> str:
        """Extract text from TXT file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            st.error(f"Error reading TXT: {str(e)}")
            return ""
    
    def extract_text_from_pdf_bytes(self, pdf_bytes: bytes) -> str:
        """Extract text from PDF bytes with robust error handling"""
        try:
            import io
            
            # Create BytesIO stream from bytes
            pdf_stream = io.BytesIO(pdf_bytes)
            
            # Try to create PDF reader
            try:
                pdf_reader = PyPDF2.PdfReader(pdf_stream)
            except Exception as reader_error:
                st.error(f"Cannot read PDF file: {str(reader_error)}")
                return ""
            
            # Check if PDF has pages
            try:
                page_count = len(pdf_reader.pages)
                if page_count == 0:
                    st.warning("PDF appears to be empty.")
                    return ""
            except Exception as page_error:
                st.error(f"Cannot access PDF pages: {str(page_error)}")
                return ""
            
            # Extract text from each page
            text = ""
            for page_num in range(page_count):
                try:
                    page = pdf_reader.pages[page_num]
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
                except Exception as page_error:
                    st.warning(f"Could not extract text from page {page_num + 1}: {str(page_error)}")
                    continue
            
            if not text.strip():
                st.warning("No text could be extracted from the PDF. It might be image-based or corrupted.")
                return ""
            
            return text
            
        except Exception as e:
            st.error(f"Error reading PDF: {str(e)}")
            return ""
    
    def extract_text_from_docx_bytes(self, docx_bytes: bytes) -> str:
        """Extract text from DOCX bytes"""
        try:
            from io import BytesIO
            doc = docx.Document(BytesIO(docx_bytes))
            text = ""
            for paragraph in doc.paragraphs:
                text += paragraph.text + "\n"
            return text
        except Exception as e:
            st.error(f"Error reading DOCX: {str(e)}")
            return ""
    
    def process_uploaded_file(self, uploaded_file) -> Optional[str]:
        """Process uploaded file and extract text"""
        if uploaded_file is None:
            return None
        
        # Process file directly from memory without saving to disk
        try:
            # Extract text based on file extension
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_extension == '.pdf':
                # Process PDF directly from bytes
                text = self.extract_text_from_pdf_bytes(uploaded_file.getvalue())
            elif file_extension == '.docx':
                # Process DOCX directly from bytes
                text = self.extract_text_from_docx_bytes(uploaded_file.getvalue())
            elif file_extension == '.txt':
                # Process TXT directly from bytes with proper encoding handling
                try:
                    text = uploaded_file.getvalue().decode('utf-8')
                except UnicodeDecodeError:
                    # Try other common encodings
                    for encoding in ['latin-1', 'cp1252', 'iso-8859-1']:
                        try:
                            text = uploaded_file.getvalue().decode(encoding)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        # If all else fails, use utf-8 with error handling
                        text = uploaded_file.getvalue().decode('utf-8', errors='replace')
            else:
                st.error(f"Unsupported file format: {file_extension}")
                return None
            
            return text
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")
            return None
    
    def split_into_chapters(self, text: str) -> Dict[str, str]:
        """Split text into chapters based on common patterns"""
        chapters = {}
        
        # Common chapter patterns
        patterns = [
            'Chapter ',
            'CHAPTER ',
            'chapter ',
            'Ch. ',
            'CH. '
        ]
        
        # Split by chapter markers
        lines = text.split('\n')
        current_chapter = "Introduction"
        current_content = []
        chapter_num = 1
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check if line starts with chapter pattern
            is_chapter_header = any(line.startswith(pattern) for pattern in patterns)
            
            if is_chapter_header:
                # Save previous chapter
                if current_content:
                    chapters[current_chapter] = '\n'.join(current_content)
                
                # Start new chapter
                current_chapter = line if line else f"Chapter {chapter_num}"
                current_content = []
                chapter_num += 1
            else:
                current_content.append(line)
        
        # Save last chapter
        if current_content:
            chapters[current_chapter] = '\n'.join(current_content)
        
        return chapters
    
    def get_chapter_summary(self, chapter_text: str) -> str:
        """Generate a brief summary of the chapter"""
        # Simple summary - first 200 words
        words = chapter_text.split()
        if len(words) > 200:
            return ' '.join(words[:200]) + "..."
        return chapter_text
