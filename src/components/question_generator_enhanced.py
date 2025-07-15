import streamlit as st
from typing import Dict, List, Optional
import json
import os
from datetime import datetime
from src.utils.mistral_api import MistralAPI
from src.utils.audio_processor import AudioProcessor
from src.config import QUESTION_TYPES, SCORING

class QuestionGenerator:
    """Handles question generation and management with enhanced features"""
    
    def __init__(self):
        self.mistral_api = MistralAPI()
        self.audio_processor = AudioProcessor()
    
    def generate_questions_for_chapter(self, chapter_text: str, chapter_name: str) -> Dict:
        """Generate all types of questions for a chapter"""
        questions = {
            'chapter_name': chapter_name,
            'timestamp': datetime.now().isoformat(),
            'mcq': [],
            '1_mark': [],
            '2_mark': [],
            '3_mark': [],
            '5_mark': []
        }
        
        # Generate MCQ questions
        with st.spinner("Generating MCQ questions..."):
            mcq_questions = self.mistral_api.generate_mcq_questions(chapter_text, num_questions=10)
            questions['mcq'] = mcq_questions
        
        # Generate subjective questions for each mark type
        for question_type in ['1_mark', '2_mark', '3_mark', '5_mark']:
            with st.spinner(f"Generating {question_type.replace('_', ' ')} questions..."):
                subjective_questions = self.mistral_api.generate_subjective_questions(
                    chapter_text, question_type, num_questions=5
                )
                questions[question_type] = subjective_questions
        
        return questions
    
    def create_custom_test(self, questions: Dict, config: Dict) -> Dict:
        """Create a custom test based on configuration"""
        custom_test = {
            'test_name': config.get('test_name', 'Custom Test'),
            'chapter_name': questions['chapter_name'],
            'timestamp': datetime.now().isoformat(),
            'time_limit': config.get('time_limit', 60),
            'questions': [],
            'total_questions': 0,
            'total_marks': 0
        }
        
        # Add questions based on configuration
        for question_type, count in config.get('question_counts', {}).items():
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
            help="Set the time limit for the test"
        )
        
        # Question selection
        st.subheader("📋 Select Questions")
        
        question_counts = {}
        total_questions = 0
        total_marks = 0
        
        for question_type in ['mcq', '1_mark', '2_mark', '3_mark', '5_mark']:
            if question_type in available_questions and available_questions[question_type]:
                available_count = len(available_questions[question_type])
                
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    count = st.slider(
                        f"{question_type.replace('_', ' ').title()} Questions:",
                        min_value=0,
                        max_value=available_count,
                        value=min(3, available_count),
                        key=f"count_{question_type}"
                    )
                
                with col2:
                    st.write(f"Available: {available_count}")
                
                question_counts[question_type] = count
                total_questions += count
                total_marks += count * SCORING.get(question_type, 1)
        
        config['question_counts'] = question_counts
        
        # Display test summary
        st.subheader("📊 Test Summary")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Questions", total_questions)
        with col2:
            st.metric("Total Marks", total_marks)
        with col3:
            st.metric("Time Limit", f"{config['time_limit']} min")
        
        return config
    
    def display_question_with_enhanced_features(self, question: Dict, question_type: str, question_index: int, total_questions: int = 0):
        """Display a question with enhanced features including audio and skip"""
        # Question header with progress
        col1, col2 = st.columns([3, 1])
        
        with col1:
            st.subheader(f"Question {question_index + 1}")
            if question_type != 'mcq':
                st.write(f"**Marks:** {SCORING.get(question_type, 1)}")
        
        with col2:
            if total_questions > 0:
                progress = (question_index + 1) / total_questions
                st.progress(progress)
                st.write(f"{question_index + 1}/{total_questions}")
        
        # Display question content
        if question_type == 'mcq':
            self._display_mcq_question(question)
        else:
            self._display_subjective_question(question)
        
        # Enhanced controls
        st.markdown("---")
        
        # Audio and interaction buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button(f"🔊 Listen", key=f"audio_{question_type}_{question_index}"):
                self._play_question_audio(question, question_type)
        
        with col2:
            if st.button(f"🎤 Voice Answer", key=f"voice_{question_type}_{question_index}"):
                return self._get_voice_answer(question_index)
        
        with col3:
            if st.button(f"⏭️ Skip", key=f"skip_{question_type}_{question_index}"):
                return "SKIP"
        
        with col4:
            if st.button(f"❓ Hint", key=f"hint_{question_type}_{question_index}"):
                self._show_hint(question, question_type)
        
        return None
    
    def _display_mcq_question(self, question: Dict):
        """Display MCQ question format"""
        st.write(f"**Question:** {question['question']}")
        st.write("**Options:**")
        
        for option, text in question['options'].items():
            st.write(f"**{option}.** {text}")
    
    def _display_subjective_question(self, question: Dict):
        """Display subjective question format"""
        st.write(f"**Question:** {question['question']}")
        
        if 'expected_length' in question:
            st.info(f"**Expected Length:** {question['expected_length']}")
        
        if 'key_points' in question:
            with st.expander("📝 Key Points to Cover"):
                for i, point in enumerate(question['key_points'], 1):
                    st.write(f"{i}. {point}")
    
    def _play_question_audio(self, question: Dict, question_type: str):
        """Play audio for a question"""
        question_text = question['question']
        
        if question_type == 'mcq':
            # Add options to audio
            options_text = " The options are: "
            for option, text in question['options'].items():
                options_text += f"Option {option}: {text}. "
            question_text += options_text
        
        # Use the audio processor to create and play TTS
        self.audio_processor.create_tts_button(
            question_text,
            "🔊 Playing...",
            f"tts_playing_{question_type}_{question.get('id', 'unknown')}"
        )
    
    def _get_voice_answer(self, question_index: int) -> Optional[str]:
        """Get voice answer from user"""
        return self.audio_processor.get_voice_input(question_index)
    
    def _show_hint(self, question: Dict, question_type: str):
        """Show hint for a question"""
        if question_type == 'mcq':
            st.info("💡 **Hint:** Read all options carefully and eliminate obviously wrong answers first.")
        else:
            if 'key_points' in question:
                st.info("💡 **Hint:** Make sure to cover these key points in your answer:")
                for point in question['key_points'][:2]:  # Show first 2 key points as hint
                    st.write(f"• {point}")
            else:
                st.info("💡 **Hint:** Structure your answer clearly with proper explanations.")
    
    def save_questions_to_file(self, questions: Dict, filename: str):
        """Save generated questions to a JSON file"""
        try:
            filepath = f"data/{filename}.json"
            os.makedirs(os.path.dirname(filepath), exist_ok=True)
            
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
                return None
            
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except Exception as e:
            st.error(f"❌ Error loading questions: {str(e)}")
            return None
    
    def get_available_question_files(self) -> List[str]:
        """Get list of available question files"""
        try:
            if not os.path.exists("data"):
                return []
            
            files = [f[:-5] for f in os.listdir("data") if f.endswith('.json') and not f.startswith('test_results')]
            return files
            
        except Exception as e:
            st.error(f"❌ Error getting question files: {str(e)}")
            return []
    
    def cleanup_audio_files(self):
        """Clean up audio files"""
        self.audio_processor.cleanup_temp_files()
