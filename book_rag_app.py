"""
Book-Based Question Generation & Assessment System
A streamlined Streamlit app for generating and evaluating questions from book chapters.
"""

import streamlit as st
import os
import json
import time
import requests
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import io
from dataclasses import dataclass
import base64

# External libraries for document processing and audio
try:
    import PyPDF2
    import pypdf
    PDF_AVAILABLE = True
except ImportError:
    PDF_AVAILABLE = False

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from gtts import gTTS
    import speech_recognition as sr
    from audio_recorder_streamlit import audio_recorder
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

try:
    from fpdf import FPDF
    PDF_EXPORT_AVAILABLE = True
except ImportError:
    PDF_EXPORT_AVAILABLE = False

# Configuration
st.set_page_config(
    page_title="Book Question Generator",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Constants
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "ELvBe6YSxK0LgKpwnz2qG4nDE0tVhO6r")
MISTRAL_BASE_URL = "https://api.mistral.ai/v1"

@dataclass
class Question:
    """Data class for storing question information"""
    text: str
    type: str
    marks: int
    options: Optional[Dict[str, str]] = None
    correct_answer: Optional[str] = None
    hint: Optional[str] = None

class DocumentProcessor:
    """Handles document processing for various file types"""
    
    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF using multiple methods"""
        text = ""
        try:
            # Method 1: PyPDF2
            if PDF_AVAILABLE:
                reader = PyPDF2.PdfReader(io.BytesIO(file_content))
                for page in reader.pages:
                    text += page.extract_text() + "\n"
            
            # Method 2: pypdf as fallback
            if not text and PDF_AVAILABLE:
                reader = pypdf.PdfReader(io.BytesIO(file_content))
                for page in reader.pages:
                    text += page.extract_text() + "\n"
                    
        except Exception as e:
            st.error(f"Error extracting PDF text: {str(e)}")
        
        return text.strip()
    
    @staticmethod
    def extract_text_from_docx(file_content: bytes) -> str:
        """Extract text from DOCX file"""
        text = ""
        try:
            if DOCX_AVAILABLE:
                doc = Document(io.BytesIO(file_content))
                for paragraph in doc.paragraphs:
                    text += paragraph.text + "\n"
        except Exception as e:
            st.error(f"Error extracting DOCX text: {str(e)}")
        
        return text.strip()
    
    @staticmethod
    def extract_text_from_txt(file_content: bytes) -> str:
        """Extract text from TXT file"""
        try:
            return file_content.decode('utf-8')
        except UnicodeDecodeError:
            try:
                return file_content.decode('latin-1')
            except Exception as e:
                st.error(f"Error reading text file: {str(e)}")
                return ""
    
    @staticmethod
    def process_uploaded_file(uploaded_file) -> str:
        """Process uploaded file and extract text"""
        if not uploaded_file:
            return ""
        
        file_content = uploaded_file.read()
        file_extension = uploaded_file.name.split('.')[-1].lower()
        
        if file_extension == 'pdf':
            return DocumentProcessor.extract_text_from_pdf(file_content)
        elif file_extension == 'docx':
            return DocumentProcessor.extract_text_from_docx(file_content)
        elif file_extension == 'txt':
            return DocumentProcessor.extract_text_from_txt(file_content)
        else:
            st.error(f"Unsupported file type: {file_extension}")
            return ""

class MistralAPI:
    """Handles Mistral AI API interactions"""
    
    @staticmethod
    def generate_questions(text: str, question_type: str, num_questions: int = 5) -> List[Question]:
        """Generate questions using Mistral AI"""
        
        if question_type == "mcq":
            prompt = f"""
            Generate {num_questions} multiple choice questions based on the following text.
            
            Text: {text[:2000]}...
            
            Return ONLY a JSON array with this exact format:
            [
                {{
                    "question": "Question text here?",
                    "options": {{
                        "A": "Option A",
                        "B": "Option B", 
                        "C": "Option C",
                        "D": "Option D"
                    }},
                    "correct_answer": "A",
                    "hint": "Brief hint"
                }}
            ]
            """
        else:
            marks = int(question_type.split('_')[0])
            prompt = f"""
            Generate {num_questions} subjective questions worth {marks} marks each based on the following text.
            
            Text: {text[:2000]}...
            
            Return ONLY a JSON array with this exact format:
            [
                {{
                    "question": "Question text here?",
                    "hint": "Brief hint for answering"
                }}
            ]
            """
        
        try:
            response = requests.post(
                f"{MISTRAL_BASE_URL}/chat/completions",
                headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
                json={
                    "model": "mistral-small",
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 1000,
                    "temperature": 0.7
                }
            )
            
            if response.status_code == 200:
                content = response.json()["choices"][0]["message"]["content"]
                
                # Extract JSON from response
                start_idx = content.find('[')
                end_idx = content.rfind(']') + 1
                
                if start_idx != -1 and end_idx != -1:
                    json_str = content[start_idx:end_idx]
                    questions_data = json.loads(json_str)
                    
                    questions = []
                    for q_data in questions_data:
                        marks = 1 if question_type == "mcq" else int(question_type.split('_')[0])
                        question = Question(
                            text=q_data["question"],
                            type=question_type,
                            marks=marks,
                            options=q_data.get("options"),
                            correct_answer=q_data.get("correct_answer"),
                            hint=q_data.get("hint")
                        )
                        questions.append(question)
                    
                    return questions
                        
        except Exception as e:
            st.error(f"Error generating questions: {str(e)}")
        
        return []
    
    @staticmethod
    def evaluate_answer(question: Question, user_answer: str) -> Dict:
        """Evaluate user's answer using Mistral AI"""
        
        if question.type == "mcq":
            # Simple comparison for MCQ
            correct = user_answer == question.correct_answer
            score = question.marks if correct else 0
            feedback = "Correct!" if correct else f"Incorrect. The correct answer is {question.correct_answer}."
            
            return {
                "score": score,
                "max_score": question.marks,
                "feedback": feedback,
                "correct": correct
            }
        else:
            # Use AI for subjective evaluation
            prompt = f"""
            Evaluate this answer for the given question. Give a score out of {question.marks} marks.
            
            Question: {question.text}
            Answer: {user_answer}
            
            Provide evaluation in JSON format:
            {{
                "score": <number>,
                "feedback": "<detailed feedback>",
                "suggestions": "<suggestions for improvement>"
            }}
            """
            
            try:
                response = requests.post(
                    f"{MISTRAL_BASE_URL}/chat/completions",
                    headers={"Authorization": f"Bearer {MISTRAL_API_KEY}"},
                    json={
                        "model": "mistral-small",
                        "messages": [{"role": "user", "content": prompt}],
                        "max_tokens": 300,
                        "temperature": 0.3
                    }
                )
                
                if response.status_code == 200:
                    content = response.json()["choices"][0]["message"]["content"]
                    
                    # Extract JSON from response
                    start_idx = content.find('{')
                    end_idx = content.rfind('}') + 1
                    
                    if start_idx != -1 and end_idx != -1:
                        json_str = content[start_idx:end_idx]
                        eval_data = json.loads(json_str)
                        
                        return {
                            "score": eval_data.get("score", 0),
                            "max_score": question.marks,
                            "feedback": eval_data.get("feedback", "No feedback available"),
                            "suggestions": eval_data.get("suggestions", ""),
                            "correct": eval_data.get("score", 0) == question.marks
                        }
                        
            except Exception as e:
                st.error(f"Error evaluating answer: {str(e)}")
            
            # Fallback evaluation
            return {
                "score": question.marks // 2,  # Give half marks as fallback
                "max_score": question.marks,
                "feedback": "Answer submitted successfully. Manual review may be needed.",
                "correct": False
            }

class AudioProcessor:
    """Handles audio-related functionality"""
    
    @staticmethod
    def text_to_speech(text: str) -> bytes:
        """Convert text to speech"""
        if not AUDIO_AVAILABLE:
            return b""
        
        try:
            # Clean text for TTS
            clean_text = text.replace("**", "").replace("*", "").strip()
            if len(clean_text) > 500:
                clean_text = clean_text[:500] + "..."
            
            tts = gTTS(text=clean_text, lang='en', slow=False)
            audio_buffer = io.BytesIO()
            tts.write_to_fp(audio_buffer)
            audio_buffer.seek(0)
            return audio_buffer.read()
        except Exception as e:
            st.error(f"Error generating speech: {str(e)}")
            return b""
    
    @staticmethod
    def speech_to_text(audio_data: bytes) -> str:
        """Convert speech to text"""
        if not AUDIO_AVAILABLE or not audio_data:
            return ""
        
        try:
            # Create a temporary file for the audio
            import tempfile
            import wave
            
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as temp_file:
                temp_file.write(audio_data)
                temp_file.flush()
                
                recognizer = sr.Recognizer()
                with sr.AudioFile(temp_file.name) as source:
                    audio = recognizer.record(source)
                
                text = recognizer.recognize_google(audio)
                
                # Clean up temp file
                os.unlink(temp_file.name)
                
                return text
        except Exception as e:
            st.error(f"Error recognizing speech: {str(e)}")
            return ""

class PDFExporter:
    """Handles PDF export functionality"""
    
    @staticmethod
    def create_questions_pdf(questions: List[Question], title: str) -> bytes:
        """Create PDF with questions"""
        if not PDF_EXPORT_AVAILABLE:
            return b""
        
        try:
            pdf = FPDF()
            pdf.add_page()
            pdf.set_font("Arial", "B", 16)
            pdf.cell(0, 10, title, ln=True, align="C")
            pdf.ln(10)
            
            for i, question in enumerate(questions, 1):
                pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, f"Question {i} ({question.marks} marks):", ln=True)
                
                pdf.set_font("Arial", "", 11)
                # Handle text encoding properly
                question_text = question.text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, question_text)
                
                if question.options:
                    pdf.ln(2)
                    for key, value in question.options.items():
                        option_text = f"{key}. {value}".encode('latin-1', 'replace').decode('latin-1')
                        pdf.cell(0, 5, option_text, ln=True)
                
                pdf.ln(5)
            
            # Get PDF output as bytes
            pdf_output = pdf.output(dest="S")
            if isinstance(pdf_output, str):
                return pdf_output.encode("latin-1")
            else:
                return bytes(pdf_output)
        except Exception as e:
            st.error(f"Error creating PDF: {str(e)}")
            return b""

def main():
    """Main application function"""
    
    st.title("📚 Book Question Generator & Assessment")
    st.markdown("Upload book chapters and generate AI-powered questions with evaluation")
    
    # Initialize session state
    if 'questions' not in st.session_state:
        st.session_state.questions = []
    if 'test_active' not in st.session_state:
        st.session_state.test_active = False
    if 'current_question' not in st.session_state:
        st.session_state.current_question = 0
    if 'user_answers' not in st.session_state:
        st.session_state.user_answers = {}
    if 'test_results' not in st.session_state:
        st.session_state.test_results = []
    
    # Sidebar navigation
    st.sidebar.title("Navigation")
    page = st.sidebar.selectbox(
        "Select Page",
        ["📁 Upload & Generate", "⚙️ Configure Test", "✍️ Take Test", "📊 Results"]
    )
    
    if page == "📁 Upload & Generate":
        upload_and_generate_page()
    elif page == "⚙️ Configure Test":
        configure_test_page()
    elif page == "✍️ Take Test":
        take_test_page()
    elif page == "📊 Results":
        results_page()

def upload_and_generate_page():
    """Upload and question generation page"""
    st.header("📁 Upload & Generate Questions")
    
    # File upload
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'docx', 'txt'],
        help="Upload your book chapter"
    )
    
    if uploaded_file:
        # Process file
        with st.spinner("Processing file..."):
            text = DocumentProcessor.process_uploaded_file(uploaded_file)
        
        if text:
            st.success(f"✅ Extracted {len(text)} characters from {uploaded_file.name}")
            
            # Show preview
            with st.expander("Preview Text"):
                st.text_area("Extracted Text", text[:500] + "..." if len(text) > 500 else text, height=200)
            
            # Question generation settings
            st.subheader("Question Generation Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                question_types = st.multiselect(
                    "Select Question Types",
                    ["mcq", "1_mark", "2_mark", "3_mark", "5_mark"],
                    default=["mcq", "2_mark"]
                )
            
            with col2:
                num_questions = st.slider("Questions per type", 1, 10, 3)
            
            if st.button("🎯 Generate Questions", type="primary"):
                if question_types:
                    all_questions = []
                    
                    progress_bar = st.progress(0)
                    total_types = len(question_types)
                    
                    for i, q_type in enumerate(question_types):
                        with st.spinner(f"Generating {q_type} questions..."):
                            questions = MistralAPI.generate_questions(text, q_type, num_questions)
                            all_questions.extend(questions)
                        
                        progress_bar.progress((i + 1) / total_types)
                    
                    st.session_state.questions = all_questions
                    
                    if all_questions:
                        st.success(f"✅ Generated {len(all_questions)} questions!")
                        
                        # Display summary
                        st.subheader("Generated Questions Summary")
                        for q_type in question_types:
                            type_questions = [q for q in all_questions if q.type == q_type]
                            st.write(f"**{q_type.replace('_', ' ').title()}**: {len(type_questions)} questions")
                        
                        # Export options
                        if PDF_EXPORT_AVAILABLE:
                            pdf_data = PDFExporter.create_questions_pdf(all_questions, f"Questions from {uploaded_file.name}")
                            if pdf_data:
                                st.download_button(
                                    "📄 Download PDF",
                                    pdf_data,
                                    f"questions_{uploaded_file.name}.pdf",
                                    "application/pdf"
                                )
                    else:
                        st.error("❌ Failed to generate questions. Please try again.")
                else:
                    st.warning("⚠️ Please select at least one question type.")

def configure_test_page():
    """Test configuration page"""
    st.header("⚙️ Configure Test")
    
    if not st.session_state.questions:
        st.warning("⚠️ No questions available. Please generate questions first.")
        return
    
    st.success(f"✅ {len(st.session_state.questions)} questions available")
    
    # Test settings
    col1, col2 = st.columns(2)
    
    with col1:
        test_name = st.text_input("Test Name", "Chapter Assessment")
        time_limit = st.number_input("Time Limit (minutes)", 5, 120, 30)
    
    with col2:
        randomize = st.checkbox("Randomize Questions", True)
        show_hints = st.checkbox("Allow Hints", True)
    
    # Question selection
    st.subheader("Select Questions")
    
    available_types = list(set(q.type for q in st.session_state.questions))
    
    selected_questions = []
    for q_type in available_types:
        type_questions = [q for q in st.session_state.questions if q.type == q_type]
        
        with st.expander(f"{q_type.replace('_', ' ').title()} Questions ({len(type_questions)} available)"):
            num_select = st.slider(
                f"Select {q_type} questions",
                0, len(type_questions), 
                min(3, len(type_questions)),
                key=f"select_{q_type}"
            )
            
            if num_select > 0:
                if randomize:
                    import random
                    selected = random.sample(type_questions, num_select)
                else:
                    selected = type_questions[:num_select]
                
                selected_questions.extend(selected)
    
    if selected_questions:
        st.info(f"📝 Selected {len(selected_questions)} questions")
        
        total_marks = sum(q.marks for q in selected_questions)
        st.metric("Total Marks", total_marks)
        
        if st.button("🚀 Start Test", type="primary"):
            st.session_state.test_questions = selected_questions
            st.session_state.test_config = {
                "name": test_name,
                "time_limit": time_limit,
                "show_hints": show_hints,
                "total_marks": total_marks
            }
            st.session_state.test_active = True
            st.session_state.current_question = 0
            st.session_state.user_answers = {}
            st.session_state.test_start_time = time.time()
            st.rerun()

def take_test_page():
    """Test taking page"""
    st.header("✍️ Take Test")
    
    if not st.session_state.test_active:
        st.warning("⚠️ No active test. Please configure a test first.")
        return
    
    if 'test_questions' not in st.session_state:
        st.error("❌ Test configuration error. Please reconfigure the test.")
        return
    
    questions = st.session_state.test_questions
    config = st.session_state.test_config
    current_idx = st.session_state.current_question
    
    # Timer with auto-refresh
    elapsed_time = time.time() - st.session_state.test_start_time
    remaining_time = (config['time_limit'] * 60) - elapsed_time
    
    if remaining_time <= 0:
        st.error("⏰ Time's up!")
        finish_test()
        return
    
    # Display timer with auto-refresh
    minutes = int(remaining_time // 60)
    seconds = int(remaining_time % 60)
    
    timer_color = "red" if remaining_time < 300 else "orange" if remaining_time < 600 else "green"
    
    # Create timer display
    timer_placeholder = st.empty()
    timer_placeholder.markdown(f"""
    <div style='text-align: center; color: {timer_color}; font-size: 24px; font-weight: bold;'>
        ⏰ Time Remaining: {minutes:02d}:{seconds:02d}
    </div>
    """, unsafe_allow_html=True)
    
    # Auto-refresh every 30 seconds to update timer
    if 'last_timer_update' not in st.session_state:
        st.session_state.last_timer_update = time.time()
    
    if time.time() - st.session_state.last_timer_update > 30:
        st.session_state.last_timer_update = time.time()
        st.rerun()
    
    # Test progress
    progress = (current_idx + 1) / len(questions)
    st.progress(progress)
    st.write(f"Question {current_idx + 1} of {len(questions)}")
    
    if current_idx >= len(questions):
        finish_test()
        return
    
    question = questions[current_idx]
    
    # Display question
    st.subheader(f"Question {current_idx + 1} ({question.marks} marks)")
    st.write(question.text)
    
    # Audio features with improved functionality
    if AUDIO_AVAILABLE:
        st.markdown("---")
        st.subheader("🎧 Audio Features")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔊 Listen to Question", use_container_width=True):
                with st.spinner("Generating audio..."):
                    audio_data = AudioProcessor.text_to_speech(question.text)
                    if audio_data:
                        st.audio(audio_data, format='audio/mp3')
                        st.success("🎵 Audio generated successfully!")
                    else:
                        st.error("❌ Failed to generate audio")
        
        with col2:
            if st.button("🎤 Record Answer", use_container_width=True):
                st.info("🎤 Click the microphone below to record your answer")
                audio_data = audio_recorder(
                    text="Click to record",
                    recording_color="#e87070",
                    neutral_color="#6aa36f",
                    icon_name="microphone",
                    icon_size="3x"
                )
                
                if audio_data:
                    st.info("🔄 Processing your voice...")
                    voice_answer = AudioProcessor.speech_to_text(audio_data)
                    if voice_answer:
                        st.session_state.user_answers[current_idx] = voice_answer
                        st.success(f"✅ Voice answer recorded: {voice_answer}")
                    else:
                        st.error("❌ Could not understand the audio. Please try again.")
        
        with col3:
            if st.button("🔍 Preview Answer", use_container_width=True):
                current_answer = st.session_state.user_answers.get(current_idx, "")
                if current_answer:
                    st.info(f"📝 Current answer: {current_answer}")
                else:
                    st.warning("⚠️ No answer recorded yet")
    
    else:
        st.warning("🔇 Audio features not available. Please install audio dependencies.")
    
    st.markdown("---")
    
    # Answer input
    user_answer = st.session_state.user_answers.get(current_idx, "")
    
    if question.type == "mcq":
        if question.options:
            answer = st.radio(
                "Select your answer:",
                list(question.options.keys()),
                format_func=lambda x: f"{x}. {question.options[x]}",
                key=f"mcq_{current_idx}"
            )
            if answer:
                st.session_state.user_answers[current_idx] = answer
    else:
        answer = st.text_area(
            "Your answer:",
            value=user_answer,
            key=f"text_{current_idx}",
            height=150
        )
        if answer:
            st.session_state.user_answers[current_idx] = answer
    
    # Hint
    if config['show_hints'] and question.hint:
        with st.expander("💡 Hint"):
            st.write(question.hint)
    
    # Navigation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if current_idx > 0:
            if st.button("⬅️ Previous"):
                st.session_state.current_question = current_idx - 1
                st.rerun()
    
    with col2:
        if current_idx < len(questions) - 1:
            if st.button("➡️ Next"):
                st.session_state.current_question = current_idx + 1
                st.rerun()
    
    with col3:
        if st.button("🏁 Finish Test"):
            finish_test()

def finish_test():
    """Finish the test and show results"""
    st.session_state.test_active = False
    
    questions = st.session_state.test_questions
    answers = st.session_state.user_answers
    
    results = []
    total_score = 0
    max_score = 0
    
    with st.spinner("Evaluating answers..."):
        for i, question in enumerate(questions):
            user_answer = answers.get(i, "")
            
            if user_answer:
                evaluation = MistralAPI.evaluate_answer(question, user_answer)
                total_score += evaluation['score']
            else:
                evaluation = {
                    'score': 0,
                    'max_score': question.marks,
                    'feedback': 'No answer provided',
                    'correct': False
                }
            
            max_score += question.marks
            results.append({
                'question': question,
                'user_answer': user_answer,
                'evaluation': evaluation
            })
    
    st.session_state.test_results = results
    st.session_state.final_score = total_score
    st.session_state.max_possible_score = max_score
    
    st.rerun()

def results_page():
    """Results display page"""
    st.header("📊 Test Results")
    
    if not st.session_state.test_results:
        st.warning("⚠️ No test results available. Please take a test first.")
        return
    
    results = st.session_state.test_results
    total_score = st.session_state.final_score
    max_score = st.session_state.max_possible_score
    
    # Overall score
    percentage = (total_score / max_score) * 100 if max_score > 0 else 0
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Score", f"{total_score}/{max_score}")
    
    with col2:
        st.metric("Percentage", f"{percentage:.1f}%")
    
    with col3:
        grade = "A" if percentage >= 90 else "B" if percentage >= 80 else "C" if percentage >= 70 else "D" if percentage >= 60 else "F"
        st.metric("Grade", grade)
    
    # Detailed results
    st.subheader("Detailed Results")
    
    for i, result in enumerate(results):
        question = result['question']
        user_answer = result['user_answer']
        evaluation = result['evaluation']
        
        with st.expander(f"Question {i+1} - Score: {evaluation['score']}/{evaluation['max_score']}"):
            st.write(f"**Question:** {question.text}")
            
            if question.type == "mcq" and question.options:
                st.write("**Options:**")
                for key, value in question.options.items():
                    st.write(f"  {key}. {value}")
                if question.correct_answer:
                    st.write(f"**Correct Answer:** {question.correct_answer}")
            
            st.write(f"**Your Answer:** {user_answer if user_answer else 'Not answered'}")
            st.write(f"**Feedback:** {evaluation['feedback']}")
            
            if 'suggestions' in evaluation and evaluation['suggestions']:
                st.write(f"**Suggestions:** {evaluation['suggestions']}")
    
    # Export results
    if PDF_EXPORT_AVAILABLE:
        if st.button("📄 Download Results PDF"):
            # Create results PDF
            st.info("PDF export feature coming soon!")
    
    # Reset for new test
    if st.button("🔄 Take New Test"):
        # Clear test-related session state
        keys_to_clear = ['test_results', 'final_score', 'max_possible_score', 
                        'test_questions', 'test_config', 'user_answers', 'current_question']
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        st.rerun()

if __name__ == "__main__":
    main()
