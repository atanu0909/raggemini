# Book Question Generator & Assessment System

A streamlined Streamlit application for generating AI-powered questions from book chapters and conducting assessments.

## Features

- **Document Processing**: Upload PDF, DOCX, or TXT files
- **AI Question Generation**: Generate MCQ and subjective questions (1-5 marks)
- **Interactive Testing**: Take tests with timer and navigation
- **Audio Support**: Text-to-speech and voice input (optional)
- **PDF Export**: Export questions to PDF format
- **Real-time Evaluation**: AI-powered answer evaluation

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements_new.txt
   ```

2. **Set up Environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your Mistral API key
   ```

3. **Run the Application**
   ```bash
   streamlit run book_rag_app.py
   ```

## Usage

1. **Upload & Generate**: Upload a book chapter and generate questions
2. **Configure Test**: Select questions and set test parameters
3. **Take Test**: Complete the test with timer and audio support
4. **View Results**: See detailed evaluation and feedback

## Requirements

- Python 3.8+
- Mistral AI API key
- Optional: Audio libraries for voice features

## Architecture

This is a single-file application that includes:
- Document processing for multiple formats
- Mistral AI integration for question generation
- Audio processing capabilities
- PDF export functionality
- Session state management

## Deployment

Deploy to Streamlit Cloud:
1. Push to GitHub repository
2. Connect to Streamlit Cloud
3. Add secrets for API keys
4. Deploy

## License

MIT License
