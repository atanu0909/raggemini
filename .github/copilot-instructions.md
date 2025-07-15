# Copilot Instructions for Book RAG System

<!-- Use this file to provide workspace-specific custom instructions to Copilot. For more details, visit https://code.visualstudio.com/docs/copilot/copilot-customization#_use-a-githubcopilotinstructionsmd-file -->

## Project Overview
This is a book-based question generation and assessment system built with Python and Streamlit. The system allows users to:
- Upload PDF/DOCX/TXT book chapters
- Generate MCQ and subjective questions (1, 2, 3, 5 marks)
- Take tests with AI-powered answer evaluation
- Support for audio questions and voice answers
- Track test history and performance

## Key Technologies
- **Frontend**: Streamlit for web interface
- **AI**: Mistral AI API for question generation and answer evaluation
- **Document Processing**: PyPDF2, python-docx for file handling
- **Audio**: gTTS for text-to-speech, SpeechRecognition for voice input
- **Data Storage**: JSON files for questions and results

## Code Structure Guidelines
- Follow Python PEP 8 style guidelines
- Use type hints for better code documentation
- Implement proper error handling with try-catch blocks
- Use Streamlit's caching mechanisms for performance
- Modular design with separate components for different functionalities

## AI Integration Notes
- All AI calls use the Mistral API with proper error handling
- Question generation includes context validation
- Answer evaluation provides detailed feedback and scoring
- Support for different question types and mark values

## Audio Features
- Text-to-speech for reading questions aloud
- Voice input for answering questions
- Proper cleanup of temporary audio files

## Security Considerations
- API keys stored in environment variables
- Input validation for file uploads
- Secure handling of user data and test results
