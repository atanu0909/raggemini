from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
import os
import tempfile
from datetime import datetime
from typing import Dict, List
import streamlit as st

class PDFExporter:
    """Handles PDF export functionality for questions and test results"""
    
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_custom_styles()
    
    def setup_custom_styles(self):
        """Set up custom styles for PDF generation"""
        # Title style
        self.title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=18,
            spaceAfter=30,
            alignment=TA_CENTER,
            textColor=colors.darkblue
        )
        
        # Question style
        self.question_style = ParagraphStyle(
            'QuestionStyle',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=10,
            leftIndent=20,
            textColor=colors.black
        )
        
        # Answer style
        self.answer_style = ParagraphStyle(
            'AnswerStyle',
            parent=self.styles['Normal'],
            fontSize=10,
            spaceAfter=5,
            leftIndent=40,
            textColor=colors.darkgreen
        )
        
        # Header style
        self.header_style = ParagraphStyle(
            'HeaderStyle',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceAfter=15,
            textColor=colors.darkblue
        )
    
    def export_questions_to_pdf(self, questions: Dict, filename: str) -> str:
        """Export questions to PDF format"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()
            
            # Create PDF document
            doc = SimpleDocTemplate(temp_file.name, pagesize=A4, topMargin=1*inch)
            story = []
            
            # Title
            title = f"Question Bank - {questions.get('chapter_name', 'Chapter')}"
            story.append(Paragraph(title, self.title_style))
            story.append(Spacer(1, 20))
            
            # Chapter info
            timestamp = questions.get('timestamp', datetime.now().isoformat())
            date_str = timestamp.split('T')[0] if 'T' in timestamp else timestamp
            story.append(Paragraph(f"Generated on: {date_str}", self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Export each question type
            question_types = ['mcq', '1_mark', '2_mark', '3_mark', '5_mark']
            
            for q_type in question_types:
                if q_type in questions and questions[q_type]:
                    # Section header
                    type_name = q_type.replace('_', ' ').title()
                    if q_type == 'mcq':
                        type_name = 'Multiple Choice Questions'
                    
                    story.append(Paragraph(f"{type_name} ({len(questions[q_type])} questions)", self.header_style))
                    story.append(Spacer(1, 10))
                    
                    # Questions
                    for i, question in enumerate(questions[q_type], 1):
                        self.add_question_to_story(story, question, q_type, i)
                        story.append(Spacer(1, 15))
                    
                    story.append(Spacer(1, 20))
            
            # Build PDF
            doc.build(story)
            
            # Move to final location
            final_path = f"data/{filename}.pdf"
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            
            import shutil
            shutil.move(temp_file.name, final_path)
            
            return final_path
            
        except Exception as e:
            st.error(f"Error exporting to PDF: {str(e)}")
            return None
    
    def add_question_to_story(self, story: List, question: Dict, q_type: str, q_number: int):
        """Add a single question to the PDF story"""
        # Question text
        q_text = f"Q{q_number}. {question['question']}"
        story.append(Paragraph(q_text, self.question_style))
        
        if q_type == 'mcq':
            # MCQ options
            for option, text in question['options'].items():
                option_text = f"{option}. {text}"
                story.append(Paragraph(option_text, self.answer_style))
            
            # Correct answer
            correct = question.get('correct_answer', 'N/A')
            story.append(Paragraph(f"<b>Correct Answer: {correct}</b>", self.answer_style))
            
            # Explanation
            if 'explanation' in question:
                story.append(Paragraph(f"<i>Explanation: {question['explanation']}</i>", self.answer_style))
        
        else:
            # Subjective question details
            marks = question.get('marks', 1)
            story.append(Paragraph(f"<b>Marks: {marks}</b>", self.answer_style))
            
            if 'expected_length' in question:
                story.append(Paragraph(f"<i>Expected Length: {question['expected_length']}</i>", self.answer_style))
            
            if 'key_points' in question:
                story.append(Paragraph("<b>Key Points:</b>", self.answer_style))
                for point in question['key_points']:
                    story.append(Paragraph(f"• {point}", self.answer_style))
    
    def export_test_results_to_pdf(self, results: List[Dict], test_info: Dict, filename: str) -> str:
        """Export test results to PDF format"""
        try:
            # Create temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.pdf')
            temp_file.close()
            
            # Create PDF document
            doc = SimpleDocTemplate(temp_file.name, pagesize=A4, topMargin=1*inch)
            story = []
            
            # Title
            title = f"Test Results - {test_info.get('test_name', 'Test')}"
            story.append(Paragraph(title, self.title_style))
            story.append(Spacer(1, 20))
            
            # Test info
            user_name = test_info.get('user_name', 'Anonymous')
            story.append(Paragraph(f"Student: {user_name}", self.styles['Normal']))
            story.append(Paragraph(f"Chapter: {test_info.get('chapter_name', 'N/A')}", self.styles['Normal']))
            story.append(Paragraph(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}", self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Summary
            total_score = sum(r.get('score', 0) for r in results)
            total_max = sum(r.get('max_score', 1) for r in results)
            percentage = (total_score / total_max * 100) if total_max > 0 else 0
            
            story.append(Paragraph("Test Summary", self.header_style))
            story.append(Paragraph(f"Total Score: {total_score}/{total_max}", self.styles['Normal']))
            story.append(Paragraph(f"Percentage: {percentage:.1f}%", self.styles['Normal']))
            story.append(Spacer(1, 20))
            
            # Individual results
            story.append(Paragraph("Detailed Results", self.header_style))
            
            for i, result in enumerate(results, 1):
                story.append(Paragraph(f"Question {i}", self.question_style))
                story.append(Paragraph(f"Score: {result.get('score', 0)}/{result.get('max_score', 1)}", self.answer_style))
                story.append(Paragraph(f"Feedback: {result.get('feedback', 'N/A')}", self.answer_style))
                story.append(Spacer(1, 10))
            
            # Build PDF
            doc.build(story)
            
            # Move to final location
            final_path = f"data/{filename}.pdf"
            os.makedirs(os.path.dirname(final_path), exist_ok=True)
            
            import shutil
            shutil.move(temp_file.name, final_path)
            
            return final_path
            
        except Exception as e:
            st.error(f"Error exporting results to PDF: {str(e)}")
            return None
    
    def create_download_link(self, file_path: str, link_text: str) -> str:
        """Create a download link for the PDF file"""
        try:
            with open(file_path, 'rb') as f:
                pdf_bytes = f.read()
            
            import base64
            b64 = base64.b64encode(pdf_bytes).decode()
            
            filename = os.path.basename(file_path)
            href = f'<a href="data:application/pdf;base64,{b64}" download="{filename}" target="_blank">{link_text}</a>'
            
            return href
            
        except Exception as e:
            st.error(f"Error creating download link: {str(e)}")
            return ""
