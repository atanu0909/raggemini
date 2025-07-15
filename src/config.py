import os
from dotenv import load_dotenv
import streamlit as st

# Load environment variables
load_dotenv()

# API Configuration - Try Streamlit secrets first, then environment variables
try:
    MISTRAL_API_KEY = st.secrets["general"]["MISTRAL_API_KEY"]
except:
    MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY", "ELvBe6YSxK0LgKpwnz2qG4nDE0tVhO6r")

MISTRAL_BASE_URL = "https://api.mistral.ai/v1"

# File Upload Configuration
UPLOAD_FOLDER = "uploads"
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.txt'}

# Question Generation Configuration
QUESTION_TYPES = {
    'mcq': 'Multiple Choice Questions',
    '1_mark': '1 Mark Questions',
    '2_mark': '2 Mark Questions', 
    '3_mark': '3 Mark Questions',
    '5_mark': '5 Mark Questions'
}

# Scoring Configuration
SCORING = {
    'mcq': 1,
    '1_mark': 1,
    '2_mark': 2,
    '3_mark': 3,
    '5_mark': 5
}

# Audio Configuration
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHUNK_SIZE = 1024

# UI Configuration
APP_TITLE = "Book-Based Question Generation & Assessment System"
APP_DESCRIPTION = "Upload book chapters and generate questions with AI-powered answer evaluation"
