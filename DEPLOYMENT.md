# Book RAG System - Deployment Notes

## Streamlit Cloud Deployment Steps

1. **GitHub Repository**: https://github.com/atanu0909/book_reading_rag
2. **Streamlit Cloud**: https://streamlit.io/cloud
3. **Deployment URL**: Will be available after deployment

## Configuration Required

### Secrets Management
In Streamlit Cloud, add these secrets:

```toml
[secrets]
MISTRAL_API_KEY = "your-mistral-api-key-here"
```

### Environment Variables
- Python version: 3.9+
- Required packages: Listed in requirements.txt

## Features
- ✅ PDF/DOCX Upload
- ✅ Chapter-wise Question Generation
- ✅ MCQ, 1-mark, 2-mark, 3-mark, 5-mark Questions
- ✅ Voice Input/Output
- ✅ Question Skipping
- ✅ Timer & Timestamps
- ✅ PDF Export
- ✅ AI-powered Answer Evaluation
- ✅ Fallback Question System

## Usage
1. Upload a book (PDF/DOCX)
2. Select question types and difficulty
3. Take the test with voice or text
4. Export results to PDF

## Technical Stack
- **Frontend**: Streamlit
- **AI**: Mistral API with fallback system
- **Audio**: audio-recorder-streamlit, gtts, speechrecognition
- **PDF**: PyPDF2, python-docx, reportlab
- **Deployment**: Streamlit Cloud
