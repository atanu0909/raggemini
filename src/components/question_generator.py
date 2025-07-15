import streamlit as st
from typing import Dict, List, Optional, Tuple
import json
import os
import time
from datetime import datetime
from src.utils.mistral_api import MistralAPI
from src.utils.audio_processor import AudioProcessor
from src.utils.pdf_exporter import PDFExporter
from src.config import QUESTION_TYPES, SCORING

class QuestionGenerator:
    """Enhanced question generation and management with customizable test options"""
    
    def __init__(self):
        self.mistral_api = MistralAPI()
        self.audio_processor = AudioProcessor()
        self.pdf_exporter = PDFExporter()
    
    def generate_questions_for_chapter(self, chapter_text: str, chapter_name: str, 
                                     custom_counts: Dict[str, int] = None) -> Dict:
        """Generate questions for a chapter with customizable quantities"""
        
        # Default question counts
        default_counts = {
            'mcq': 10,
            '1_mark': 8,
            '2_mark': 6,
            '3_mark': 5,
            '5_mark': 4
        }
        
        # Use custom counts if provided
        counts = custom_counts if custom_counts else default_counts
        
        questions = {
            'chapter_name': chapter_name,
            'created_at': datetime.now().isoformat(),
            'mcq': [],
            '1_mark': [],
            '2_mark': [],
            '3_mark': [],
            '5_mark': []
        }
        
        # Progress tracking
        total_questions = sum(counts.values())
        progress_bar = st.progress(0)
        progress_text = st.empty()
        current_progress = 0
        
        # Generate each type of question
        for question_type, count in counts.items():
            if count > 0:
                progress_text.text(f"Generating {question_type.replace('_', ' ')} questions...")
                
                if question_type == 'mcq':
                    new_questions = self.mistral_api.generate_mcq_questions(
                        chapter_text, num_questions=count
                    )
                else:
                    new_questions = self.mistral_api.generate_subjective_questions(
                        chapter_text, question_type, num_questions=count
                    )
                
                questions[question_type] = new_questions
                current_progress += count
                progress_bar.progress(current_progress / total_questions)
        
        progress_bar.empty()
        progress_text.empty()
        
        return questions
    
    def create_custom_test(self, questions: Dict, test_config: Dict) -> Dict:
        """Create a custom test based on user preferences"""
        
        custom_test = {
            'test_name': test_config.get('test_name', 'Custom Test'),
            'created_at': datetime.now().isoformat(),
            'time_limit': test_config.get('time_limit', 60),  # minutes
            'total_questions': 0,
            'total_marks': 0,
            'questions': []
        }
        
        # Add questions based on configuration
        for question_type, count in test_config.get('question_counts', {}).items():
            if count > 0 and question_type in questions:
                available_questions = questions[question_type]
                selected_questions = available_questions[:count]
                
                for q in selected_questions:
                    custom_test['questions'].append({
                        'question': q,
                        'type': question_type,
                        'marks': SCORING.get(question_type, 1)
                    })
                
                custom_test['total_questions'] += len(selected_questions)
                custom_test['total_marks'] += len(selected_questions) * SCORING.get(question_type, 1)
        
        return custom_test
    
    def display_test_configuration(self, available_questions: Dict) -> Dict:
        """Display test configuration interface"""
        st.subheader("🎯 Test Configuration")
        
        config = {}
        
        # Test name
        config['test_name'] = st.text_input(
            "Test Name:", 
            value=f"Test - {datetime.now().strftime('%Y-%m-%d %H:%M')}"
        )
        
        # Time limit
        config['time_limit'] = st.slider(
            "Time Limit (minutes):", 
            min_value=15, 
            max_value=180, 
            value=60, 
            step=15
        )
        
        # Question selection
        st.write("**Select Questions:**")
        
        question_counts = {}
        total_questions = 0
        total_marks = 0
        
        # Create columns for different question types
        cols = st.columns(5)
        
        for i, (q_type, display_name) in enumerate(QUESTION_TYPES.items()):
            with cols[i]:
                available_count = len(available_questions.get(q_type, []))
                
                if available_count > 0:
                    count = st.number_input(
                        f"{display_name}",
                        min_value=0,
                        max_value=available_count,
                        value=min(5, available_count),
                        key=f"count_{q_type}"
                    )
                    
                    question_counts[q_type] = count
                    total_questions += count
                    total_marks += count * SCORING.get(q_type, 1)
                    
                    st.write(f"Available: {available_count}")
                    st.write(f"Marks: {count * SCORING.get(q_type, 1)}")
                else:
                    st.write(f"{display_name}: 0 available")
                    question_counts[q_type] = 0
        
        config['question_counts'] = question_counts
        
        # Display test summary
        st.write("---")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Questions", total_questions)
        with col2:
            st.metric("Total Marks", total_marks)
        with col3:
            st.metric("Time Limit", f"{config['time_limit']} min")
        
        return config
    
    def display_question_with_enhanced_features(self, question_data: Dict, 
                                              question_index: int, 
                                              total_questions: int,
                                              start_time: float) -> Tuple[str, bool]:
        """Display question with enhanced features including audio and skip options"""
        
        question = question_data['question']
        question_type = question_data['type']
        marks = question_data['marks']
        
        # Header with question info
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader(f"Question {question_index + 1} of {total_questions}")
        
        with col2:
            st.write(f"**Type:** {question_type.replace('_', ' ').title()}")
        
        with col3:
            st.write(f"**Marks:** {marks}")
        
        # Time tracking
        elapsed_time = time.time() - start_time
        remaining_time = max(0, (st.session_state.get('time_limit', 60) * 60) - elapsed_time)
        
        if remaining_time > 0:
            minutes = int(remaining_time // 60)
            seconds = int(remaining_time % 60)
            st.write(f"⏱️ Time Remaining: {minutes:02d}:{seconds:02d}")
        else:
            st.error("⏰ Time's up!")
            return None, True
        
        # Display question content
        self._display_question_content(question, question_type)
        
        # Audio controls
        audio_played, voice_answer = self.audio_processor.display_audio_controls(
            self._get_question_text_for_audio(question, question_type),
            question_index
        )
        
        # Answer input
        user_answer = self._get_user_answer(question, question_type, question_index, voice_answer)
        
        # Navigation and control buttons
        col1, col2, col3, col4 = st.columns(4)
        
        skipped = False
        
        with col1:
            if question_index > 0:
                if st.button("⬅️ Previous", key=f"prev_{question_index}"):
                    return None, False
        
        with col2:
            if st.button("⏭️ Skip Question", key=f"skip_{question_index}"):
                skipped = True
        
        with col3:
            if user_answer and st.button("✅ Submit", key=f"submit_{question_index}", type="primary"):
                return user_answer, False
        
        with col4:
            if st.button("� Finish Test", key=f"finish_{question_index}"):
                st.session_state['force_finish'] = True
                return None, True
        
        return None if skipped else user_answer, skipped
    
    def _display_question_content(self, question: Dict, question_type: str):
        """Display question content based on type"""
        
        st.write(f"**Question:** {question['question']}")
        
        if question_type == 'mcq':
            st.write("**Options:**")
            for option, text in question['options'].items():
                st.write(f"**{option}.** {text}")
        else:
            if 'expected_length' in question:
                st.write(f"**Expected Length:** {question['expected_length']}")
            
            if 'key_points' in question and question['key_points']:
                with st.expander("💡 Key Points to Consider"):
                    for point in question['key_points']:
                        st.write(f"• {point}")
    
    def _get_question_text_for_audio(self, question: Dict, question_type: str) -> str:
        """Get formatted question text for audio"""
        text = question['question']
        
        if question_type == 'mcq':
            text += " The options are: "
            for option, option_text in question['options'].items():
                text += f"Option {option}: {option_text}. "
        
        return text
    
    def _get_user_answer(self, question: Dict, question_type: str, 
                        question_index: int, voice_answer: str) -> Optional[str]:
        """Get user answer with multiple input methods"""
        
        if voice_answer:
            st.success("✅ Voice answer recorded!")
            st.write(f"**Your voice answer:** {voice_answer}")
            return voice_answer
        
        if question_type == 'mcq':
            return st.radio(
                "Select your answer:",
                options=list(question['options'].keys()),
                key=f"mcq_{question_index}",
                horizontal=True
            )
        else:
            return st.text_area(
                "Enter your answer:",
                height=150,
                key=f"text_{question_index}",
                help="Type your detailed answer here"
            )
    
    def save_questions_to_file(self, questions: Dict, filename: str):
        """Save generated questions to a JSON file with metadata"""
        try:
            os.makedirs("data", exist_ok=True)
            filepath = f"data/{filename}.json"
            
            # Add metadata
            questions['saved_at'] = datetime.now().isoformat()
            questions['version'] = '2.0'
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(questions, f, indent=2, ensure_ascii=False)
            
            st.success(f"✅ Questions saved to {filepath}")
            
        except Exception as e:
            st.error(f"❌ Error saving questions: {str(e)}")
    
    def load_questions_from_file(self, filename: str) -> Optional[Dict]:
        """Load questions from a JSON file"""
        try:
            filepath = f"data/{filename}.json"
            
            if not os.path.exists(filepath):
                st.error(f"File not found: {filepath}")
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                questions = json.load(f)
            
            # Show metadata if available
            if 'created_at' in questions:
                st.info(f"📅 Created: {questions['created_at']}")
            
            return questions
                
        except Exception as e:
            st.error(f"❌ Error loading questions: {str(e)}")
            return None
    
    def get_available_question_files(self) -> List[Dict]:
        """Get list of available question files with metadata"""
        try:
            if not os.path.exists("data"):
                return []
            
            files = []
            for filename in os.listdir("data"):
                if filename.endswith('.json') and not filename.startswith('test_results_'):
                    filepath = f"data/{filename}"
                    try:
                        with open(filepath, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        
                        # Count questions
                        total_questions = sum(len(data.get(q_type, [])) for q_type in QUESTION_TYPES.keys())
                        
                        files.append({
                            'filename': filename[:-5],  # Remove .json
                            'display_name': data.get('chapter_name', filename[:-5]),
                            'created_at': data.get('created_at', 'Unknown'),
                            'total_questions': total_questions,
                            'file_path': filepath
                        })
                    except:
                        continue
            
            # Sort by creation date (newest first)
            files.sort(key=lambda x: x['created_at'], reverse=True)
            return files
            
        except Exception as e:
            st.error(f"❌ Error getting question files: {str(e)}")
            return []
    
    def export_questions_to_pdf(self, questions: Dict, filename: str) -> str:
        """Export questions to PDF format"""
        try:
            pdf_path = self.pdf_exporter.export_questions_to_pdf(questions, filename)
            if pdf_path:
                st.success(f"✅ Questions exported to PDF: {pdf_path}")
                return pdf_path
            else:
                st.error("❌ Failed to export questions to PDF")
                return None
        except Exception as e:
            st.error(f"❌ Error exporting to PDF: {str(e)}")
            return None
    
    def create_pdf_download_button(self, questions: Dict, filename: str):
        """Create a download button for PDF export"""
        if st.button("📄 Export Questions to PDF", key=f"pdf_export_{filename}"):
            with st.spinner("Generating PDF..."):
                try:
                    # Generate PDF in memory
                    pdf_bytes = self.pdf_exporter.export_questions_to_pdf_bytes(questions, filename)
                    
                    if pdf_bytes:
                        st.download_button(
                            label="📥 Download PDF",
                            data=pdf_bytes,
                            file_name=f"{filename}_questions.pdf",
                            mime="application/pdf",
                            key=f"download_{filename}"
                        )
                        st.success("✅ PDF generated successfully!")
                    else:
                        st.error("❌ Failed to generate PDF")
                        
                except Exception as e:
                    st.error(f"❌ Error generating PDF: {str(e)}")
                    
                    # Fallback: Create a simple text download
                    try:
                        text_content = self._create_text_format(questions)
                        st.download_button(
                            label="� Download as Text (Fallback)",
                            data=text_content,
                            file_name=f"{filename}_questions.txt",
                            mime="text/plain",
                            key=f"download_text_{filename}"
                        )
                        st.info("PDF generation failed, but text version is available.")
                    except:
                        st.error("All export methods failed.")
    
    def _create_text_format(self, questions: Dict) -> str:
        """Create a text format of questions as fallback"""
        text = f"Questions Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
        text += "=" * 50 + "\n\n"
        
        for category, question_list in questions.items():
            if category in ['mcq', '1_mark', '2_mark', '3_mark', '5_mark'] and question_list:
                text += f"{category.upper()} QUESTIONS:\n"
                text += "-" * 20 + "\n"
                
                for i, q in enumerate(question_list, 1):
                    text += f"{i}. {q.get('question', '')}\n"
                    if 'options' in q:
                        for opt in q['options']:
                            text += f"   {opt}\n"
                        text += f"   Answer: {q.get('answer', '')}\n"
                    else:
                        text += f"   Answer: {q.get('answer', '')}\n"
                    text += "\n"
                text += "\n"
        
        return text
    
    def cleanup_audio_files(self):
        """Clean up audio files"""
        self.audio_processor.cleanup_temp_files()
