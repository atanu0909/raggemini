import speech_recognition as sr
import pydub
from gtts import gTTS
import os
import tempfile
import streamlit as st
from typing import Optional
import base64
import time
import io
import wave
from audio_recorder_streamlit import audio_recorder

class AudioProcessor:
    """Enhanced audio processing for speech recognition and text-to-speech"""
    
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.temp_files = []  # Keep track of temp files for cleanup
    
    def text_to_speech(self, text: str, language: str = 'en') -> Optional[str]:
        """Convert text to speech and return audio file path"""
        try:
            # Clean text for better TTS
            clean_text = self._clean_text_for_tts(text)
            
            # Create TTS object
            tts = gTTS(text=clean_text, lang=language, slow=False)
            
            # Save to temporary file
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
            tts.save(temp_file.name)
            
            # Track temp file for cleanup
            self.temp_files.append(temp_file.name)
            
            return temp_file.name
            
        except Exception as e:
            st.error(f"Error in text-to-speech: {str(e)}")
            return None
    
    def _clean_text_for_tts(self, text: str) -> str:
        """Clean text for better text-to-speech conversion"""
        import re
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove special characters that might cause TTS issues
        text = re.sub(r'[^\w\s\.\,\!\?\-\:\;]', '', text)
        
        # Limit length for better performance
        if len(text) > 500:
            text = text[:500] + "..."
        
        return text.strip()
    
    def speech_to_text(self, audio_bytes: bytes) -> Optional[str]:
        """Convert speech to text from audio bytes"""
        try:
            # Save audio bytes to temporary file
            temp_audio_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            temp_audio_file.write(audio_bytes)
            temp_audio_file.close()
            
            # Convert audio to proper format using pydub
            audio = pydub.AudioSegment.from_file(temp_audio_file.name)
            
            # Convert to WAV format for better recognition
            wav_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            audio.export(wav_file.name, format='wav')
            wav_file.close()
            
            # Convert to text using speech recognition
            with sr.AudioFile(wav_file.name) as source:
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                audio_data = self.recognizer.record(source)
                text = self.recognizer.recognize_google(audio_data)
                
            # Clean up temp files
            os.unlink(temp_audio_file.name)
            os.unlink(wav_file.name)
            
            return text
            
        except sr.UnknownValueError:
            st.error("⚠️ Could not understand the audio. Please try speaking more clearly.")
            return None
        except sr.RequestError as e:
            st.error(f"⚠️ Speech recognition service error: {str(e)}")
            return None
        except Exception as e:
            st.error(f"⚠️ Error in speech-to-text: {str(e)}")
            return None
    
    def get_voice_input(self, question_index: int) -> Optional[str]:
        """Get voice input with improved UI using streamlit-audiorecorder"""
        st.write("🎤 **Voice Answer Mode**")
        st.info("Click the record button below to record your answer. Speak clearly and wait for the recording to complete.")
        
        # Create unique key for this question
        recorder_key = f"voice_recorder_{question_index}"
        
        # Use audio_recorder for recording
        audio_bytes = audio_recorder(
            text="Click to record",
            recording_color="#e8b62c",
            neutral_color="#6aa36f",
            icon_name="microphone",
            icon_size="2x",
            key=recorder_key
        )
        
        if audio_bytes:
            st.success("✅ Recording completed! Converting to text...")
            
            # Convert to text
            with st.spinner("🔄 Processing your voice..."):
                text = self.speech_to_text(audio_bytes)
            
            if text:
                st.success("✅ Voice converted to text successfully!")
                st.write(f"**Your answer:** {text}")
                
                # Ask for confirmation
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Use this answer", key=f"confirm_{question_index}"):
                        return text
                with col2:
                    if st.button("🔄 Record again", key=f"retry_{question_index}"):
                        st.rerun()
            else:
                st.error("❌ Could not convert speech to text. Please try again.")
                if st.button("🔄 Try again", key=f"retry_audio_{question_index}"):
                    st.rerun()
        
        return None
    
    def create_audio_player(self, audio_file_path: str) -> str:
        """Create HTML audio player for Streamlit"""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                audio_bytes = audio_file.read()
                audio_base64 = base64.b64encode(audio_bytes).decode()
                
            audio_html = f"""
            <audio controls style="width: 100%;">
                <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                Your browser does not support the audio element.
            </audio>
            """
            return audio_html
            
        except Exception as e:
            st.error(f"Error creating audio player: {str(e)}")
            return ""
    
    def play_audio_in_streamlit(self, audio_file_path: str):
        """Display audio player in Streamlit"""
        try:
            with open(audio_file_path, 'rb') as audio_file:
                st.audio(audio_file.read(), format='audio/mp3')
        except Exception as e:
            st.error(f"Error playing audio: {str(e)}")
    
    def cleanup_temp_files(self):
        """Clean up temporary audio files"""
        for file_path in self.temp_files:
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
            except Exception as e:
                st.warning(f"Could not delete temp file {file_path}: {str(e)}")
        
        self.temp_files.clear()
    
    def create_tts_button(self, text: str, button_text: str, key: str):
        """Create a button that plays TTS when clicked"""
        if st.button(button_text, key=key):
            audio_file = self.text_to_speech(text)
            if audio_file:
                self.play_audio_in_streamlit(audio_file)
                # Clean up immediately after playing
                try:
                    os.unlink(audio_file)
                except:
                    pass
    
    def __del__(self):
        """Cleanup when object is destroyed"""
        self.cleanup_temp_files()
