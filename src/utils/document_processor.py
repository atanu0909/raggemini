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
    
    def process_uploaded_file(self, uploaded_file) -> Optional[str]:
        """Process uploaded file and extract text"""
        if uploaded_file is None:
            return None
        
        # Create temporary file
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(uploaded_file.name)[1]) as temp_file:
            temp_file.write(uploaded_file.getbuffer())
            temp_path = temp_file.name
        
        try:
            # Extract text based on file extension
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            
            if file_extension == '.pdf':
                text = self.extract_text_from_pdf(temp_path)
            elif file_extension == '.docx':
                text = self.extract_text_from_docx(temp_path)
            elif file_extension == '.txt':
                text = self.extract_text_from_txt(temp_path)
            else:
                st.error(f"Unsupported file format: {file_extension}")
                return None
            
            return text
        finally:
            # Clean up temporary file
            if os.path.exists(temp_path):
                os.remove(temp_path)
    
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
