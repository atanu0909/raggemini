"""
Book-Based Question Generation & Assessment System
A streamlined Streamlit app for generating and evaluating questions from book chapters.
"""

import streamlit as st
import google.generativeai as genai
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
    PYPDF2_AVAILABLE = True
except ImportError:
    PYPDF2_AVAILABLE = False

try:
    import pypdf
    PYPDF_AVAILABLE = True
except ImportError:
    PYPDF_AVAILABLE = False

# For older pypdf versions, try alternative import
if not PYPDF_AVAILABLE:
    try:
        import pyPdf as pypdf
        PYPDF_AVAILABLE = True
    except ImportError:
        PYPDF_AVAILABLE = False

PDF_AVAILABLE = PYPDF2_AVAILABLE or PYPDF_AVAILABLE

try:
    from docx import Document
    DOCX_AVAILABLE = True
except ImportError:
    DOCX_AVAILABLE = False

try:
    from gtts import gTTS
    import speech_recognition as sr
    from audio_recorder_streamlit import audio_recorder
    import tempfile
    import wave
    from pydub import AudioSegment
    from pydub.utils import make_chunks
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

# Model API Keys
MISTRAL_API_KEY = st.secrets.get("MISTRAL_API_KEY") or os.getenv("MISTRAL_API_KEY")
MISTRAL_BASE_URL = "https://api.mistral.ai/v1"
GEMINI_API_KEY = st.secrets.get("GEMINI_API_KEY") or os.getenv("GEMINI_API_KEY")

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
    
    # PyMuPDF availability handled at top

    @staticmethod
    def extract_text_from_pdf(file_content: bytes) -> str:
        """Extract text from PDF using PyMuPDF (fitz) if available, else fallback to PyPDF2/pypdf"""
        text = ""
        extraction_methods = []
        st.info("🔍 Starting PDF text extraction...")

        # Method 0: Try PyMuPDF (fitz) first for text and diagrams
        try:
            import fitz
            doc = fitz.open(stream=file_content, filetype="pdf")
            st.info(f"📄 Found {doc.page_count} pages in PDF (PyMuPDF)")
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                page_text = page.get_text("text")
                if page_text and page_text.strip():
                    text += page_text + "\n"
                    st.success(f"✅ Extracted text from page {page_num + 1} (PyMuPDF)")
                else:
                    st.warning(f"⚠️ No text found on page {page_num + 1} (PyMuPDF)")
            if text.strip():
                extraction_methods.append("PyMuPDF")
                st.success(f"✅ PyMuPDF extraction successful! Extracted {len(text)} characters")
        except ImportError:
            st.warning("⚠️ PyMuPDF not available")
        except Exception as e:
            st.warning(f"❌ PyMuPDF failed: {str(e)}")

        # Fallback to PyPDF2/pypdf if PyMuPDF fails or no text
        if not text.strip():
            pass

        # Clean up extracted text
        if text.strip():
            text = ' '.join(text.split())
            text = text.replace('\n\n', '\n').replace('\n', ' ').strip()
            st.success(f"🎉 PDF processing complete!")
            st.info(f"📊 Final statistics:")
            st.info(f"  • Methods used: {', '.join(extraction_methods)}")
            st.info(f"  • Characters extracted: {len(text)}")
            st.info(f"  • Words extracted: {len(text.split())}")
            return text
        else:
            st.error("❌ Could not extract text from PDF")
            st.error("🔍 Possible reasons:")
            st.error("  • PDF contains only images/scanned content (needs OCR)")
            st.error("  • PDF is password protected or encrypted")
            st.error("  • PDF file is corrupted or has invalid format")
            st.error("  • Text is embedded as images rather than searchable text")
            st.error("💡 Suggestions:")
            st.error("  • Try converting the PDF to text format first")
            st.error("  • Use an OCR tool for scanned documents")
            st.error("  • Check if the PDF opens correctly in other applications")
            st.error("  • Try uploading a different PDF file")
            return ""

    @staticmethod
    def extract_images_from_pdf(file_content: bytes) -> list:
        """Extract images/diagrams from PDF using PyMuPDF (fitz)"""
        images = []
        try:
            import fitz
            doc = fitz.open(stream=file_content, filetype="pdf")
            for page_num in range(doc.page_count):
                page = doc.load_page(page_num)
                for img in page.get_images(full=True):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    images.append(image_bytes)
            return images
        except ImportError:
            st.warning("⚠️ PyMuPDF not available for image extraction")
        except Exception as e:
            st.warning(f"❌ PyMuPDF image extraction failed: {str(e)}")
        return []
    
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
        
        try:
            # Reset file pointer to beginning
            uploaded_file.seek(0)
            file_content = uploaded_file.read()
            
            # Check if file is empty
            if not file_content:
                st.error("❌ The uploaded file is empty.")
                return ""
            
            file_extension = uploaded_file.name.split('.')[-1].lower()
            
            st.info(f"📄 Processing {file_extension.upper()} file: {uploaded_file.name}")
            st.info(f"📏 File size: {len(file_content)} bytes")
            
            if file_extension == 'pdf':
                if not PDF_AVAILABLE:
                    st.error("❌ PDF processing libraries not available. Please install PyPDF2 and pypdf.")
                    return ""
                return DocumentProcessor.extract_text_from_pdf(file_content)
            elif file_extension == 'docx':
                if not DOCX_AVAILABLE:
                    st.error("❌ DOCX processing library not available. Please install python-docx.")
                    return ""
                return DocumentProcessor.extract_text_from_docx(file_content)
            elif file_extension == 'txt':
                return DocumentProcessor.extract_text_from_txt(file_content)
            else:
                st.error(f"❌ Unsupported file type: {file_extension}")
                st.error("✅ Supported formats: PDF, DOCX, TXT")
                return ""
                
        except Exception as e:
            st.error(f"❌ Error processing file: {str(e)}")
            return ""


# Unified AI API for Mistral and Gemini
class AIModelAPI:
    """Handles both Mistral and Gemini AI API interactions"""
    @staticmethod
    def generate_questions(text: str, question_type: str, num_questions: int = 5, model_choice: str = "Mistral") -> List[Question]:
        """Generate questions using selected AI model"""
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
            if model_choice == "Gemini":
                genai.configure(api_key=GEMINI_API_KEY)
                model = genai.GenerativeModel('gemini-2.5-flash')
                response = model.generate_content(prompt)
                content = response.text
            else:
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
                else:
                    st.error(f"Mistral API error: {response.text}")
                    return []

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
    def evaluate_answer(question: Question, user_answer: str, model_choice: str = "Mistral") -> Dict:
        """Evaluate user's answer using selected AI model and subject context"""
        subject = st.session_state.get("selected_subject", "General Knowledge")
        # Use custom evaluation rule if present
        custom_rule = st.session_state.get("custom_eval_rule", "").strip()
        if question.type == "mcq":
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
            # Subject-specific evaluation prompt
            subject_focus = {
                "Maths": "Focus on formulas, calculation steps, and final answer accuracy.",
                "Chemistry": "Focus on chemical formulas, reaction steps, and correct terminology.",
                "Physics": "Focus on concepts, formulas, and logical steps.",
                "History": "Focus on names, locations, dates, and historical accuracy.",
                "English": "Focus on grammar, vocabulary, and answer relevance.",
                "Geography": "Focus on locations, facts, and map-related details.",
                "Economics": "Focus on concepts, definitions, and economic reasoning.",
                "Computer": "Focus on technical accuracy, code, and logic.",
                "Story/Fables": "Focus on narrative, characters, and moral lessons.",
                "Newspaper": "Focus on facts, reporting style, and clarity.",
                "General Knowledge": "Focus on factual correctness and clarity."
            }
            if custom_rule:
                focus_text = custom_rule
            else:
                focus_text = subject_focus.get(subject, subject_focus["General Knowledge"])
            prompt = f"""
            Evaluate this answer for the given question. Subject: {subject}. {focus_text}
            Give a score out of {question.marks} marks.
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
                if model_choice == "Gemini":
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    response = model.generate_content(prompt)
                    content = response.text
                else:
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
                    else:
                        st.error(f"Mistral API error: {response.text}")
                        return {
                            "score": 0,
                            "max_score": question.marks,
                            "feedback": "API error.",
                            "correct": False
                        }
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
            return {
                "score": question.marks // 2,
                "max_score": question.marks,
                "feedback": "Answer submitted successfully. Manual review may be needed.",
                "correct": False
            }

class AudioProcessor:
    """Handles audio-related functionality with multiple recognition engines"""
    
    @staticmethod
    def text_to_speech(text: str) -> bytes:
        """Convert text to speech"""
        if not AUDIO_AVAILABLE:
            return b""
        
        try:
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
    def simple_speech_to_text(audio_data: bytes) -> str:
        """Simple speech to text without pydub as fallback"""
        if not AUDIO_AVAILABLE or not audio_data:
            return ""
        
        import uuid
        temp_file = None
        
        try:
            # Create unique temporary file
            temp_filename = f"temp_audio_{uuid.uuid4().hex}.wav"
            temp_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False, prefix=temp_filename)
            temp_file.write(audio_data)
            temp_file.flush()
            temp_file.close()  # Close file handle before using it
            
            recognizer = sr.Recognizer()
            with sr.AudioFile(temp_file.name) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio = recognizer.record(source)
            
            try:
                result = recognizer.recognize_google(audio)
                return result
            except sr.UnknownValueError:
                st.warning("Could not understand the audio")
                return ""
            except sr.RequestError as e:
                st.error(f"Google Speech Recognition service error: {e}")
                return ""
                
        except Exception as e:
            st.error(f"Error processing audio: {str(e)}")
            return ""
        
        finally:
            # Clean up temporary file
            if temp_file and os.path.exists(temp_file.name):
                try:
                    os.unlink(temp_file.name)
                except:
                    pass
    
    @staticmethod
    def speech_to_text_with_pydub(audio_data: bytes) -> str:
        """Convert speech to text using pydub for better audio handling"""
        if not AUDIO_AVAILABLE or not audio_data:
            return ""
        
        import uuid
        input_file = None
        output_file = None
        
        try:
            # Create unique temporary files
            input_filename = f"temp_input_{uuid.uuid4().hex}.wav"
            output_filename = f"temp_output_{uuid.uuid4().hex}.wav"
            
            input_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False, prefix=input_filename)
            input_file.write(audio_data)
            input_file.flush()
            input_file.close()
            
            # Load audio with pydub (with fallback)
            try:
                # Try without ffmpeg first
                audio = AudioSegment.from_wav(input_file.name)
            except:
                try:
                    # Try with general file loader
                    audio = AudioSegment.from_file(input_file.name)
                except Exception as e:
                    st.warning(f"Pydub audio loading failed: {str(e)}")
                    # Fall back to simple method
                    return AudioProcessor.simple_speech_to_text(audio_data)
            
            # Convert to standard format for better recognition
            audio = audio.set_channels(1)  # Mono
            audio = audio.set_frame_rate(16000)  # 16kHz
            audio = audio.set_sample_width(2)  # 16-bit
            
            # Normalize audio
            audio = audio.normalize()
            
            # Save processed audio
            output_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False, prefix=output_filename)
            output_file.close()
            
            audio.export(output_file.name, format="wav")
            
            # Use speech recognition on processed audio
            recognizer = sr.Recognizer()
            with sr.AudioFile(output_file.name) as source:
                recognizer.adjust_for_ambient_noise(source, duration=0.2)
                audio_sr = recognizer.record(source)
            
            # Try recognition
            try:
                result = recognizer.recognize_google(audio_sr)
                if result:
                    st.success("✅ Advanced audio processing successful!")
                    return result
            except sr.UnknownValueError:
                st.warning("⚠️ Could not understand processed audio")
            except sr.RequestError as e:
                st.warning(f"⚠️ Google Speech service error: {e}")
            except Exception as e:
                st.warning(f"⚠️ Recognition error: {e}")
            
            return ""
                    
        except Exception as e:
            st.error(f"Error processing audio with pydub: {str(e)}")
            return ""
        
        finally:
            # Clean up temporary files
            if input_file and os.path.exists(input_file.name):
                try:
                    os.unlink(input_file.name)
                except:
                    pass
            if output_file and os.path.exists(output_file.name):
                try:
                    os.unlink(output_file.name)
                except:
                    pass
    
    @staticmethod
    def smart_speech_to_text(audio_data: bytes) -> str:
        """Smart speech to text that tries pydub first, then falls back to simple method"""
        if not AUDIO_AVAILABLE or not audio_data:
            return ""
        
        # Try pydub method first (better quality)
        try:
            st.info("🔄 Trying advanced audio processing...")
            result = AudioProcessor.speech_to_text_with_pydub(audio_data)
            if result and result.strip():
                st.success("✅ Advanced audio processing successful!")
                return result.strip()
            else:
                st.warning("⚠️ Advanced processing returned empty result")
        except Exception as e:
            st.warning(f"Advanced audio processing failed: {str(e)}")
            st.info("🔄 Falling back to simple audio processing...")
        
        # Fall back to simple method
        try:
            result = AudioProcessor.simple_speech_to_text(audio_data)
            if result and result.strip():
                st.success("✅ Simple audio processing successful!")
                return result.strip()
            else:
                st.warning("⚠️ Simple processing returned empty result")
        except Exception as e:
            st.error(f"Simple audio processing failed: {str(e)}")
        
        st.error("❌ All speech recognition methods failed")
        return ""
    
    @staticmethod
    def process_audio_file(uploaded_audio_file) -> str:
        """Process uploaded audio file using pydub for format conversion"""
        if not AUDIO_AVAILABLE or not uploaded_audio_file:
            return ""
        
        import uuid
        temp_input_file = None
        temp_output_file = None
        
        try:
            # Create unique temporary file for input
            input_filename = f"temp_input_{uuid.uuid4().hex}.{uploaded_audio_file.name.split('.')[-1]}"
            temp_input_file = tempfile.NamedTemporaryFile(suffix=f'.{uploaded_audio_file.name.split(".")[-1]}', delete=False, prefix=input_filename)
            temp_input_file.write(uploaded_audio_file.read())
            temp_input_file.flush()
            temp_input_file.close()
            
            # Load audio with pydub (supports many formats)
            try:
                st.info(f"🔄 Loading {uploaded_audio_file.name}...")
                audio = AudioSegment.from_file(temp_input_file.name)
                
                # Show audio information
                st.info(f"📊 Audio info: {audio.duration_seconds:.2f}s, {audio.frame_rate}Hz, {audio.channels} channels")
                
                # Convert to optimal format for speech recognition
                st.info("🔄 Converting to optimal format...")
                audio = audio.set_channels(1)  # Mono
                audio = audio.set_frame_rate(16000)  # 16kHz
                audio = audio.set_sample_width(2)  # 16-bit
                
                # Normalize and clean audio
                audio = audio.normalize()
                audio = audio.strip_silence(silence_thresh=-40)
                
                # If audio is too long, split into chunks
                if audio.duration_seconds > 60:
                    st.info("🔄 Audio is long, processing in chunks...")
                    chunk_length_ms = 30000  # 30 seconds
                    chunks = make_chunks(audio, chunk_length_ms)
                    
                    full_text = ""
                    for i, chunk in enumerate(chunks):
                        if len(chunk) > 1000:  # Skip very short chunks
                            st.info(f"🔄 Processing chunk {i+1}/{len(chunks)}...")
                            
                            chunk_file = None
                            try:
                                chunk_filename = f"temp_chunk_{uuid.uuid4().hex}.wav"
                                chunk_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False, prefix=chunk_filename)
                                chunk_file.close()
                                
                                chunk.export(chunk_file.name, format="wav")
                                
                                recognizer = sr.Recognizer()
                                try:
                                    with sr.AudioFile(chunk_file.name) as source:
                                        recognizer.adjust_for_ambient_noise(source, duration=0.2)
                                        audio_sr = recognizer.record(source)
                                    
                                    chunk_text = recognizer.recognize_google(audio_sr)
                                    if chunk_text:
                                        full_text += chunk_text + " "
                                        st.success(f"✅ Chunk {i+1} processed")
                                    
                                except Exception as e:
                                    st.warning(f"⚠️ Chunk {i+1} failed: {str(e)}")
                                
                            finally:
                                if chunk_file and os.path.exists(chunk_file.name):
                                    try:
                                        os.unlink(chunk_file.name)
                                    except:
                                        pass
                    
                    return full_text.strip()
                
                else:
                    # Process single audio file
                    output_filename = f"temp_output_{uuid.uuid4().hex}.wav"
                    temp_output_file = tempfile.NamedTemporaryFile(suffix='.wav', delete=False, prefix=output_filename)
                    temp_output_file.close()
                    
                    audio.export(temp_output_file.name, format="wav")
                    
                    recognizer = sr.Recognizer()
                    with sr.AudioFile(temp_output_file.name) as source:
                        recognizer.adjust_for_ambient_noise(source, duration=0.2)
                        audio_sr = recognizer.record(source)
                    
                    # Try recognition
                    try:
                        result = recognizer.recognize_google(audio_sr)
                        return result
                    except sr.UnknownValueError:
                        st.error("Could not understand the audio file")
                    except sr.RequestError as e:
                        st.error(f"Google Speech Recognition service error: {e}")
                    
                    return ""
            
            except Exception as e:
                st.error(f"Audio processing error: {str(e)}")
                return ""
                
        except Exception as e:
            st.error(f"Error processing audio file: {str(e)}")
            return ""
        
        finally:
            # Clean up temporary files
            if temp_input_file and os.path.exists(temp_input_file.name):
                try:
                    os.unlink(temp_input_file.name)
                except:
                    pass
            if temp_output_file and os.path.exists(temp_output_file.name):
                try:
                    os.unlink(temp_output_file.name)
                except:
                    pass
    
    @staticmethod
    def create_audio_interface(question_text: str, current_idx: int) -> str:
        """Create comprehensive audio interface"""
        user_answer = ""
        
        if not AUDIO_AVAILABLE:
            st.warning("🔇 Audio features not available. Please install audio dependencies.")
            return ""
        
        st.markdown("---")
        st.subheader("🎧 Audio Features")
        
        # Create tabs for different audio options
        tab1, tab2, tab3 = st.tabs(["🔊 Listen", "🎤 Record", "📁 Upload Audio"])
        
        with tab1:
            st.markdown("**Listen to the question:**")
            if st.button("🔊 Play Question Audio", key=f"play_{current_idx}"):
                with st.spinner("Generating audio..."):
                    audio_data = AudioProcessor.text_to_speech(question_text)
                    if audio_data:
                        st.audio(audio_data, format='audio/mp3')
                        st.success("🎵 Audio generated successfully!")
                    else:
                        st.error("❌ Failed to generate audio")
        
        with tab2:
            st.markdown("**Record your answer:**")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🎤 Start Recording", key=f"record_{current_idx}"):
                    st.info("🎤 Click the microphone below to record your answer")
                    audio_data = audio_recorder(
                        text="Click to record",
                        recording_color="#e87070",
                        neutral_color="#6aa36f",
                        icon_name="microphone",
                        icon_size="3x",
                        key=f"recorder_{current_idx}"
                    )
                    
                    if audio_data:
                        st.info("🔄 Processing your voice...")
                        with st.spinner("Converting speech to text..."):
                            voice_answer = AudioProcessor.smart_speech_to_text(audio_data)
                        
                        if voice_answer:
                            st.success(f"✅ Voice answer recorded!")
                            st.info(f"📝 Recognized text: {voice_answer}")
                            user_answer = voice_answer
                        else:
                            st.error("❌ Could not understand the audio. Please try again.")
            
            with col2:
                # Manual audio recording with improved interface
                st.markdown("**Or use the recorder below:**")
                audio_bytes = audio_recorder(
                    text="Record Answer",
                    recording_color="#ff6b6b",
                    neutral_color="#4ecdc4",
                    icon_name="microphone-alt",
                    icon_size="2x",
                    key=f"manual_recorder_{current_idx}"
                )
                
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/wav")
                    
                    if st.button("🔤 Convert to Text", key=f"convert_{current_idx}"):
                        with st.spinner("Converting speech to text..."):
                            voice_answer = AudioProcessor.smart_speech_to_text(audio_bytes)
                        
                        if voice_answer:
                            st.success(f"✅ Conversion successful!")
                            st.text_area("Recognized Text:", voice_answer, key=f"recognized_{current_idx}")
                            user_answer = voice_answer
                        else:
                            st.error("❌ Could not understand the audio. Please try speaking clearly.")
        
        with tab3:
            st.markdown("**Upload an audio file:**")
            st.info("📤 Supported formats: WAV, MP3, M4A, FLAC")
            
            uploaded_audio = st.file_uploader(
                "Choose an audio file",
                type=['wav', 'mp3', 'm4a', 'flac'],
                key=f"audio_upload_{current_idx}"
            )
            
            if uploaded_audio:
                st.audio(uploaded_audio, format=f"audio/{uploaded_audio.name.split('.')[-1]}")
                
                if st.button("🔤 Process Audio File", key=f"process_audio_{current_idx}"):
                    with st.spinner("Processing uploaded audio..."):
                        file_answer = AudioProcessor.process_audio_file(uploaded_audio)
                    
                    if file_answer:
                        st.success(f"✅ Audio file processed successfully!")
                        st.text_area("Transcribed Text:", file_answer, key=f"transcribed_{current_idx}")
                        user_answer = file_answer
                    else:
                        st.error("❌ Could not process the audio file. Please try a different file.")
        
        return user_answer

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
                question_text = question.text.encode('latin-1', 'replace').decode('latin-1')
                pdf.multi_cell(0, 5, question_text)
                
                if question.options:
                    pdf.ln(2)
                    for key, value in question.options.items():
                        option_text = f"{key}. {value}".encode('latin-1', 'replace').decode('latin-1')
                        pdf.cell(0, 5, option_text, ln=True)
                
                pdf.ln(5)
            
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
    # --- Custom UI ---
    st.markdown("""
        <style>
        .atanu-header {
            background: linear-gradient(90deg, #4e54c8 0%, #8f94fb 100%);
            color: white;
            padding: 24px 0 12px 0;
            border-radius: 0 0 16px 16px;
            text-align: center;
            font-size: 2.2rem;
            font-weight: bold;
            letter-spacing: 2px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .atanu-sub {
            color: #222;
            font-size: 1.1rem;
            text-align: center;
            margin-bottom: 0.5rem;
        }
        .atanu-guidelines {
            background: #f7f7fa;
            border-radius: 12px;
            padding: 18px;
            margin-bottom: 1.5rem;
            box-shadow: 0 1px 4px rgba(0,0,0,0.04);
        }
        .atanu-dark .atanu-header { background: linear-gradient(90deg, #232526 0%, #414345 100%); color: #fff; }
        .atanu-dark .atanu-guidelines { background: #232526; color: #eee; }
        </style>
    """, unsafe_allow_html=True)

    # Dark/Light mode toggle
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = False
    dark_mode = st.sidebar.checkbox("🌗 Dark Mode", value=st.session_state.dark_mode, key="dark_mode_toggle")
    st.session_state.dark_mode = dark_mode
    st.markdown(f'<div class="atanu-header {"atanu-dark" if dark_mode else ""}">Book Question Generator & Assessment<br><span style="font-size:1.2rem;font-weight:normal;">by ATANU GHOSH</span></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="atanu-sub {"atanu-dark" if dark_mode else ""}">Welcome! This platform is designed for students and educators to generate, take, and evaluate book-based questions with AI.</div>', unsafe_allow_html=True)

    # Guidelines section (always visible, not in expander)
    guidelines_class = "atanu-guidelines atanu-dark" if dark_mode else "atanu-guidelines"
    guidelines_text_color = "#eee" if dark_mode else "#222"
    st.markdown(f"""
    <div class='{guidelines_class}'>
    <ul style='color: {guidelines_text_color}; font-size: 1.08rem; font-weight: 500;'>
    <li>Upload chapters in PDF, DOCX, or TXT format.</li>
    <li>Select your subject for tailored evaluation (Maths, Chemistry, English, etc.).</li>
    <li>Generate MCQ and subjective questions (1, 2, 3, 5 marks).</li>
    <li>Answer via text, audio, or handwriting image (Gemini-powered OCR).</li>
    <li>Take tests and get instant AI feedback and scoring.</li>
    <li>Track your test history and performance.</li>
    <li>All data is securely handled. API keys are never exposed.</li>
    <li>Switch between Dark/Light mode for comfort.</li>
    </ul>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar navigation
    st.sidebar.title("Navigation")
    st.sidebar.markdown("---")
    if 'model_choice' not in st.session_state:
        st.session_state.model_choice = "Mistral"
    st.session_state.model_choice = st.sidebar.selectbox(
        "Select AI Model",
        ["Mistral", "Gemini"],
        index=0 if st.session_state.model_choice == "Mistral" else 1
    )
    page = st.sidebar.selectbox(
        "Select Page",
        ["📁 Upload & Generate", "⚙️ Configure Test", "✍️ Take Test", "📊 Results"]
    )

    # Page routing
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
    
    # Show system status
    with st.expander("🔧 System Status"):
        col1, col2, col3 = st.columns(3)
        with col1:
            st.write("**PDF Processing:**")
            if PYPDF2_AVAILABLE:
                st.success("✅ PyPDF2 Available")
            else:
                st.error("❌ PyPDF2 Not Available")
            
            if PYPDF_AVAILABLE:
                pypdf_version = "old pyPdf" if hasattr(pypdf, 'PdfFileReader') else "new pypdf"
                st.success(f"✅ pypdf Available ({pypdf_version})")
            else:
                st.error("❌ pypdf Not Available")
                
            if PDF_AVAILABLE:
                st.success("✅ PDF Processing Ready")
            else:
                st.error("❌ No PDF Libraries Available")
        
        with col2:
            st.write("**DOCX Processing:**")
            if DOCX_AVAILABLE:
                st.success("✅ Available")
            else:
                st.error("❌ Not available")
        
        with col3:
            st.write("**Audio Features:**")
            if AUDIO_AVAILABLE:
                st.success("✅ Available")
            else:
                st.warning("⚠️ Not available")
    
    # File upload
    st.subheader("Select Subject")
    subject_options = [
        "English", "Chemistry", "Physics", "Geography", "Economics", "Maths", "Computer", "Story/Fables", "Newspaper", "General Knowledge", "History"
    ]
    st.selectbox(
        "Which subject are you uploading?",
        subject_options,
        key="selected_subject"
    )

    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['pdf', 'docx', 'txt'],
        help="Upload your book chapter (PDF, DOCX, or TXT format)"
    )
    
    # Sample text for testing
    st.markdown("---")
    st.subheader("🧪 Test with Sample Text")
    if st.button("📝 Use Sample Text"):
        sample_text = """
        The history of artificial intelligence (AI) began in antiquity, with myths, stories and rumors of artificial beings endowed with intelligence or consciousness by master craftsmen. The seeds of modern AI were planted by classical philosophers who attempted to describe the process of human thinking as the mechanical manipulation of symbols. This work culminated in the invention of the programmable digital computer in the 1940s, a machine based on the abstract essence of mathematical reasoning. This device and the ideas behind it inspired a handful of scientists to begin seriously discussing the possibility of building an electronic brain.
        
        The field of AI research was born at a workshop at Dartmouth College in 1956, where the term "artificial intelligence" was coined. The participants of this workshop predicted that machines would soon be able to perform any intellectual task that a human being could do. This optimism, however, was short-lived. The early years of AI were characterized by both remarkable achievements and significant setbacks.
        
        Machine learning, a subset of AI, focuses on the development of algorithms that can learn and improve from experience without being explicitly programmed. This approach has become increasingly important in recent years, with applications ranging from image recognition to natural language processing.
        """
        
        st.session_state.sample_text = sample_text
        st.success("✅ Sample text loaded! You can now generate questions.")
        
        # Show sample text
        with st.expander("📖 Sample Text Preview"):
            st.text_area("Sample Text", sample_text, height=200)
        
        # Question generation for sample text
        st.subheader("Generate Questions from Sample Text")
        
        col1, col2 = st.columns(2)
        
        with col1:
            question_types = st.multiselect(
                "Select Question Types",
                ["mcq", "1_mark", "2_mark", "3_mark", "5_mark"],
                default=["mcq", "2_mark"],
                key="sample_question_types"
            )
        
        with col2:
            num_questions = st.slider("Questions per type", 1, 10, 3, key="sample_num_questions")
        
        if st.button("🎯 Generate Questions from Sample", type="primary"):
            if question_types:
                all_questions = []
                progress_bar = st.progress(0)
                total_types = len(question_types)
                for i, q_type in enumerate(question_types):
                    with st.spinner(f"Generating {q_type} questions..."):
                        questions = AIModelAPI.generate_questions(sample_text, q_type, num_questions, st.session_state.model_choice)
                        all_questions.extend(questions)
                    progress_bar.progress((i + 1) / total_types)
                st.session_state.questions = all_questions
                if all_questions:
                    st.success(f"✅ Generated {len(all_questions)} questions!")
                    st.subheader("Generated Questions Summary")
                    for q_type in question_types:
                        type_questions = [q for q in all_questions if q.type == q_type]
                        st.write(f"**{q_type.replace('_', ' ').title()}**: {len(type_questions)} questions")
                else:
                    st.error("❌ Failed to generate questions. Please try again.")
            else:
                st.warning("⚠️ Please select at least one question type.")
    
    st.markdown("---")
    
    if uploaded_file:
        # Display file information
        st.info(f"📁 File selected: {uploaded_file.name}")
        st.info(f"📏 File size: {uploaded_file.size} bytes")
        
        # Check file size (limit to 10MB)
        if uploaded_file.size > 10 * 1024 * 1024:
            st.error("❌ File too large. Please upload a file smaller than 10MB.")
            return
        
        # PDF-specific debugging
        if uploaded_file.name.lower().endswith('.pdf'):
            st.info("🔍 PDF file detected - performing initial validation...")
            
            # Read first few bytes to check if it's a valid PDF
            uploaded_file.seek(0)
            first_bytes = uploaded_file.read(10)
            uploaded_file.seek(0)  # Reset for processing
            
            if first_bytes.startswith(b'%PDF-'):
                st.success("✅ Valid PDF file format detected")
                pdf_version = first_bytes.decode('utf-8', errors='ignore')
                st.info(f"📄 PDF version: {pdf_version}")
            else:
                st.error("❌ Invalid PDF file format")
                st.error("The file does not appear to be a valid PDF document")
                return
        
        # Process file
        with st.spinner("Processing file..."):
            text = DocumentProcessor.process_uploaded_file(uploaded_file)
        
        if text:
            st.success(f"✅ Successfully extracted {len(text)} characters from {uploaded_file.name}")
            
            # Show text quality check
            if len(text) < 100:
                st.warning("⚠️ Extracted text is very short. Please check if the file contains readable text.")
            
            # Show preview
            with st.expander("📖 Preview Extracted Text"):
                preview_text = text[:1000] + "..." if len(text) > 1000 else text
                st.text_area("Extracted Text", preview_text, height=200)
                
                # Show text statistics
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Characters", len(text))
                with col2:
                    st.metric("Words", len(text.split()))
                with col3:
                    st.metric("Lines", len(text.split('\n')))
            
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
                            questions = AIModelAPI.generate_questions(text, q_type, num_questions, st.session_state.model_choice)
                            all_questions.extend(questions)
                        progress_bar.progress((i + 1) / total_types)
                    st.session_state.questions = all_questions
                    if all_questions:
                        st.success(f"✅ Generated {len(all_questions)} questions!")
                        st.subheader("Generated Questions Summary")
                        for q_type in question_types:
                            type_questions = [q for q in all_questions if q.type == q_type]
                            st.write(f"**{q_type.replace('_', ' ').title()}**: {len(type_questions)} questions")
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
        else:
            st.error("❌ Failed to extract text from the uploaded file.")
            st.info("💡 Try the following:")
            st.info("• Make sure the file is not corrupted")
            st.info("• For PDFs, ensure they contain text (not just images)")
            st.info("• Try converting to TXT format first")
            st.info("• Check if the file is password protected")

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
    
    # --- Custom Evaluation Rule Section ---
    st.markdown("---")
    st.subheader("Custom Evaluation Rule (Optional)")
    custom_rule = st.text_area("Write your custom evaluation rule here (overrides subject rule)", value=st.session_state.get("custom_eval_rule", ""), key="custom_eval_rule")
    uploaded_rule_pdf = st.file_uploader("Or upload a PDF with your custom evaluation rule", type=["pdf"], key="custom_eval_rule_pdf")
    rule_text = ""
    if uploaded_rule_pdf:
        # Extract text from PDF
        rule_text = DocumentProcessor.extract_text_from_pdf(uploaded_rule_pdf.read())
        if rule_text:
            st.success("✅ Custom rule loaded from PDF!")
            st.text_area("Extracted Rule from PDF", rule_text, height=120, key="custom_eval_rule_pdf_preview")
            st.session_state["custom_eval_rule"] = rule_text
        else:
            st.error("❌ Could not extract text from PDF.")
    elif custom_rule.strip():
        st.session_state["custom_eval_rule"] = custom_rule.strip()
    else:
        if "custom_eval_rule" not in st.session_state:
            st.session_state["custom_eval_rule"] = ""
    
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
    
    # Display timer
    minutes = int(remaining_time // 60)
    seconds = int(remaining_time % 60)
    
    timer_color = "red" if remaining_time < 300 else "orange" if remaining_time < 600 else "green"
    
    st.markdown(f"""
    <div style='text-align: center; color: {timer_color}; font-size: 24px; font-weight: bold;'>
        ⏰ Time Remaining: {minutes:02d}:{seconds:02d}
    </div>
    """, unsafe_allow_html=True)
    
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
    audio_answer = AudioProcessor.create_audio_interface(question.text, current_idx)
    
    # If audio answer was captured, use it
    if audio_answer:
        st.session_state.user_answers[current_idx] = audio_answer
    
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
        st.markdown("**Choose your answer input method:**")
        input_tabs = st.tabs(["Text", "Audio", "Handwriting Image"])

        # Text input
        with input_tabs[0]:
            answer = st.text_area(
                "Your answer:",
                value=user_answer,
                key=f"text_{current_idx}",
                height=150
            )
            if answer:
                st.session_state.user_answers[current_idx] = answer

        # Audio input (already handled above)
        with input_tabs[1]:
            st.info("Use the audio interface above to record or upload your answer.")

        # Handwriting image input
        with input_tabs[2]:
            st.markdown("**Upload an image of your handwritten answer:**")
            uploaded_img = st.file_uploader(
                "Choose an image file (JPG, PNG)",
                type=["jpg", "jpeg", "png"],
                key=f"handwriting_img_{current_idx}"
            )
            if uploaded_img:
                from PIL import Image
                import google.generativeai as genai
                try:
                    genai.configure(api_key=GEMINI_API_KEY)
                    model = genai.GenerativeModel('gemini-2.5-flash')
                    image = Image.open(uploaded_img)
                    input_prompt = "Rewrite the handwritten answer in the image as text."
                    with st.spinner("Transcribing handwriting with Gemini..."):
                        response = model.generate_content([input_prompt, image])
                        handwriting_text = response.text
                    if handwriting_text:
                        st.success("✅ Handwriting transcribed!")
                        st.text_area("Transcribed Text:", handwriting_text, key=f"handwriting_text_{current_idx}")
                        st.session_state.user_answers[current_idx] = handwriting_text
                    else:
                        st.error("❌ Could not transcribe handwriting. Try a clearer image.")
                except Exception as e:
                    st.error(f"Error processing handwriting image: {str(e)}")
    
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
                evaluation = AIModelAPI.evaluate_answer(question, user_answer, st.session_state.model_choice)
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

